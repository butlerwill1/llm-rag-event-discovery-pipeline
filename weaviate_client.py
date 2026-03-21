"""
Weaviate vector database client for semantic event storage and retrieval.
"""

import os
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
from openai import OpenAI
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class WeaviateEventStore:
    """Manages event storage and retrieval in Weaviate vector database."""
    
    def __init__(self, host: str = None, port: int = None, grpc_port: int = None):
        """
        Initialize Weaviate client (v4 API).

        Args:
            host: Weaviate host (defaults to env var WEAVIATE_HOST or 'localhost')
            port: Weaviate HTTP port (defaults to env var WEAVIATE_PORT or 8080)
            grpc_port: Weaviate gRPC port (defaults to env var WEAVIATE_GRPC_PORT or 50051)
        """
        host = host or os.getenv("WEAVIATE_HOST", "localhost")
        port = port or int(os.getenv("WEAVIATE_PORT", "8080"))
        grpc_port = grpc_port or int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))

        # Use Weaviate v4 client initialization
        self.client = weaviate.connect_to_local(
            host=host,
            port=port,
            grpc_port=grpc_port,
            additional_config=weaviate.classes.init.AdditionalConfig(
                timeout=(10, 60)  # (connection_timeout, read_timeout) in seconds
            )
        )

        # Initialize local embedding model (free, no API calls needed!)
        # Using all-MiniLM-L6-v2: fast, lightweight (80MB), good quality
        logger.info("Loading local embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Local embedding model loaded successfully")

        # Keep OpenAI client for LLM-based duplicate detection
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create Event collection if it doesn't exist (v4 API)."""
        # Check if collection exists
        if self.client.collections.exists("Event"):
            logger.info("Event collection already exists")
            return

        # Create collection with properties (v4 API)
        # Note: No vectorizer configured - we handle vectorization via OpenAI API in Python
        self.client.collections.create(
            name="Event",
            description="London events found by AI agent",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(
                    name="eventName",
                    data_type=DataType.TEXT,
                    description="Name of the event"
                ),
                Property(
                    name="eventDate",
                    data_type=DataType.DATE,
                    description="Date and time of the event"
                ),
                Property(
                    name="eventType",
                    data_type=DataType.TEXT,
                    description="Type/category of event"
                ),
                Property(
                    name="eventUrl",
                    data_type=DataType.TEXT,
                    description="URL to event details",
                    skip_vectorization=True,
                    tokenization=wvc.config.Tokenization.FIELD
                ),
                Property(
                    name="description",
                    data_type=DataType.TEXT,
                    description="Event description"
                ),
                Property(
                    name="ticketPrice",
                    data_type=DataType.TEXT,
                    description="Ticket price information"
                ),
                Property(
                    name="venue",
                    data_type=DataType.TEXT,
                    description="Event venue/location"
                ),
                Property(
                    name="speakers",
                    data_type=DataType.TEXT,
                    description="Event speakers or performers"
                ),
                Property(
                    name="dateLogged",
                    data_type=DataType.DATE,
                    description="When this event was found by the agent"
                )
            ]
        )
        logger.info("Created Event collection in Weaviate")
    
    def add_event(self, event: Dict[str, Any]) -> str:
        """
        Add an event to Weaviate.

        Args:
            event: Event dictionary with keys matching schema

        Returns:
            UUID of created object
        """
        # Helper function to convert dates to RFC3339 format
        def to_rfc3339(date_str: str) -> str:
            """Convert date string to RFC3339 format with timezone."""
            if not date_str:
                return ""

            try:
                # If it's already a full datetime with timezone, return as-is
                if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
                    return date_str

                # If it's a datetime without timezone (e.g., "2026-03-18T14:15:41.024894")
                if 'T' in date_str:
                    # Add UTC timezone
                    return date_str + 'Z'

                # If it's just a date (e.g., "2026-03-01")
                # Convert to datetime at midnight UTC
                return date_str + 'T00:00:00Z'

            except Exception as e:
                logger.warning(f"Failed to convert date '{date_str}': {e}")
                return date_str

        # Prepare data object
        properties = {
            "eventName": event.get("event_name", ""),
            "eventDate": to_rfc3339(event.get("event_date", "")),
            "eventType": event.get("event_type", ""),
            "eventUrl": event.get("event_url", ""),
            "description": event.get("description", ""),
            "ticketPrice": event.get("ticket_price", ""),
            "venue": event.get("venue", ""),
            "speakers": event.get("speakers", ""),
            "dateLogged": to_rfc3339(datetime.now().isoformat())
        }

        # Generate embedding locally (no API calls!)
        # Combine the most important fields for semantic search
        text_to_embed = f"{event.get('event_name', '')} {event.get('description', '')} {event.get('event_type', '')} {event.get('venue', '')}"
        vector = self.embedding_model.encode(text_to_embed).tolist()

        logger.debug(f"Generated {len(vector)}-dimensional embedding for event")

        # Add to Weaviate (v4 API) with vector
        events = self.client.collections.get("Event")
        uuid = events.data.insert(
            properties=properties,
            vector=vector  # Include the locally-generated embedding
        )

        logger.info(f"Added event to Weaviate: {event.get('event_name')} (UUID: {uuid})")
        return str(uuid)

    def is_duplicate(self, event: Dict[str, Any], use_llm: bool = True) -> bool:
        """
        Check if event is a duplicate using RAG-powered LLM decision.

        Args:
            event: Event to check
            use_llm: If True, use LLM for intelligent deduplication. If False, use simple similarity.

        Returns:
            True if duplicate found, False otherwise
        """
        logger.info(f"🔍 Checking for duplicates: {event.get('event_name')}")

        # Method 1: Exact URL match (fast path - always check this first)
        events = self.client.collections.get("Event")
        url_results = events.query.fetch_objects(
            filters=wvc.query.Filter.by_property("eventUrl").equal(event.get("event_url", "")),
            limit=1
        )

        if len(url_results.objects) > 0:
            logger.info(f"   ✓ Duplicate found (exact URL match)")
            return True

        # Method 2: RAG-powered LLM deduplication
        if use_llm:
            return self._is_duplicate_with_llm(event)
        else:
            # Fallback: Simple semantic similarity
            return self._is_duplicate_simple(event)

    def _is_duplicate_simple(self, event: Dict[str, Any], similarity_threshold: float = 0.90) -> bool:
        """Simple semantic similarity check without LLM using local embeddings."""
        search_text = f"{event.get('event_name', '')} {event.get('description', '')}"

        # Generate query embedding locally
        query_vector = self.embedding_model.encode(search_text).tolist()

        events = self.client.collections.get("Event")
        results = events.query.near_vector(
            near_vector=query_vector,
            certainty=similarity_threshold,
            limit=1
        )

        if len(results.objects) > 0:
            similar_event = results.objects[0]
            logger.info(f"✓ Duplicate found (semantic similarity): {event.get('event_name')} "
                       f"similar to {similar_event.properties['eventName']}")
            return True

        return False

    def _is_duplicate_with_llm(self, event: Dict[str, Any]) -> bool:
        """
        Use RAG + LLM to intelligently determine if event is duplicate.
        More accurate than simple similarity threshold.
        Uses local embeddings for retrieval.
        """
        # 1. Retrieve similar events (cast wider net with lower threshold)
        search_text = f"{event.get('event_name', '')} {event.get('description', '')}"

        logger.info(f"   🔎 Searching for similar events in database...")

        # Generate query embedding locally
        query_vector = self.embedding_model.encode(search_text).tolist()

        events = self.client.collections.get("Event")
        results = events.query.near_vector(
            near_vector=query_vector,
            certainty=0.85,  # Lower threshold to catch more candidates
            limit=5  # Get top 5 similar events
        )

        if len(results.objects) == 0:
            logger.info(f"   ✗ No similar events found in database")
            return False

        logger.info(f"   📊 Found {len(results.objects)} similar event(s) in database")

        # Convert to dict format for compatibility with existing code
        similar_events = [obj.properties for obj in results.objects]

        # 2. Build context for LLM
        context = self._format_similar_events_for_llm(similar_events)

        # 3. Ask LLM to decide
        # Note: Using gpt-4o for deduplication (not gpt-5) because:
        # - Deduplication is a simpler task that doesn't need reasoning capabilities
        # - gpt-4o is faster and more cost-effective for this use case
        # - gpt-5 is reserved for complex agentic web search
        logger.info(f"   🤖 Asking LLM (gpt-4o) to analyze similarity...")

        prompt = f"""You are an expert at identifying duplicate events.

            New Event Being Checked:
            - Name: {event.get('event_name', 'N/A')}
            - Date: {event.get('event_date', 'N/A')}
            - URL: {event.get('event_url', 'N/A')}
            - Type: {event.get('event_type', 'N/A')}
            - Venue: {event.get('venue', 'N/A')}
            - Description: {event.get('description', 'N/A')[:300]}

            Potentially Similar Events in Database:
            {context}

            Question: Is the new event a DUPLICATE of any existing event?

            Rules for determining duplicates:
            1. Same event name/topic AND same date = DUPLICATE
            2. Same URL = DEFINITELY DUPLICATE
            3. Similar name but DIFFERENT date = NOT duplicate (could be recurring event)
            4. Similar topic but different organizer/venue = NOT duplicate
            5. Same event series but different edition/year = NOT duplicate

            Answer ONLY with valid JSON (no markdown, no code blocks):
            {{"is_duplicate": true, "reason": "explanation", "matching_event": "name"}}
            OR
            {{"is_duplicate": false, "reason": "explanation", "matching_event": null}}"""

        try:
            # Use gpt-4o for deduplication - it's faster and cheaper than gpt-5
            # Deduplication is a simpler task that doesn't need reasoning capabilities
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistent decisions
            )

            result = json.loads(response.choices[0].message.content)

            if result.get("is_duplicate"):
                logger.info(f"   ✓ LLM Decision: DUPLICATE")
                logger.info(f"      Reason: {result.get('reason')}")
                logger.info(f"      Matches: {result.get('matching_event')}")
                return True
            else:
                logger.info(f"   ✗ LLM Decision: NOT a duplicate")
                logger.info(f"      Reason: {result.get('reason')}")
                return False

        except Exception as e:
            logger.error(f"LLM deduplication failed, falling back to simple similarity: {e}")
            return self._is_duplicate_simple(event)

    def _format_similar_events_for_llm(self, events: List[Dict[str, Any]]) -> str:
        """Format similar events for LLM context."""
        formatted = []
        for i, event in enumerate(events, 1):
            formatted.append(
                f"{i}. {event.get('eventName', 'N/A')}\n"
                f"   Date: {event.get('eventDate', 'N/A')}\n"
                f"   URL: {event.get('eventUrl', 'N/A')}\n"
                f"   Type: {event.get('eventType', 'N/A')}\n"
                f"   Venue: {event.get('venue', 'N/A')}\n"
                f"   Description: {event.get('description', 'N/A')[:200]}..."
            )
        return "\n\n".join(formatted)

    def get_all_events(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve all events from Weaviate.

        Args:
            limit: Maximum number of events to retrieve

        Returns:
            List of event dictionaries
        """
        events = self.client.collections.get("Event")
        results = events.query.fetch_objects(limit=limit)

        # Convert to standard format
        return [
            {
                "event_name": obj.properties.get("eventName"),
                "event_date": obj.properties.get("eventDate"),
                "event_type": obj.properties.get("eventType"),
                "event_url": obj.properties.get("eventUrl"),
                "description": obj.properties.get("description"),
                "ticket_price": obj.properties.get("ticketPrice"),
                "venue": obj.properties.get("venue"),
                "speakers": obj.properties.get("speakers"),
                "date_logged": obj.properties.get("dateLogged")
            }
            for obj in results.objects
        ]

    def search_events(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for events using local embeddings.

        Args:
            query: Natural language query
            limit: Maximum number of results

        Returns:
            List of matching events
        """
        # Generate query embedding locally
        query_vector = self.embedding_model.encode(query).tolist()

        events = self.client.collections.get("Event")
        results = events.query.near_vector(
            near_vector=query_vector,
            limit=limit
        )

        return [
            {
                "event_name": obj.properties.get("eventName"),
                "event_date": obj.properties.get("eventDate"),
                "event_type": obj.properties.get("eventType"),
                "event_url": obj.properties.get("eventUrl"),
                "description": obj.properties.get("description"),
                "ticket_price": obj.properties.get("ticketPrice"),
                "venue": obj.properties.get("venue"),
                "speakers": obj.properties.get("speakers")
            }
            for obj in results.objects
        ]

    def get_event_count(self) -> int:
        """Get total number of events in database."""
        events = self.client.collections.get("Event")
        # Use len() on the collection to get the count
        return len(events)

    def cleanup_past_events(self) -> int:
        """
        Delete events that occurred before today's date to save storage and costs.

        Returns:
            Number of events deleted
        """
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Cleaning up events with eventDate before {today}")

        # Get events with eventDate before today
        try:
            events = self.client.collections.get("Event")
            results = events.query.fetch_objects(
                filters=wvc.query.Filter.by_property("eventDate").less_than(today + "T00:00:00Z"),
                limit=1000  # Process in batches
            )

            if len(results.objects) == 0:
                logger.info("No old events to clean up")
                return 0

            # Delete each old event using batch delete
            deleted_count = 0
            for obj in results.objects:
                try:
                    events.data.delete_by_id(obj.uuid)
                    deleted_count += 1
                    logger.debug(f"Deleted: {obj.properties.get('eventName')} ({obj.properties.get('eventDate')})")
                except Exception as e:
                    logger.warning(f"Failed to delete event {obj.properties.get('eventName')}: {e}")
                    continue

            logger.info(f"✓ Cleaned up {deleted_count} past events")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup past events: {e}")
            return 0

    def get_events_since(self, since_date: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get events added since a specific date.

        Args:
            since_date: ISO format date string (e.g., "2025-01-12T00:00:00Z")
            limit: Max events to return

        Returns:
            List of events
        """
        events = self.client.collections.get("Event")
        results = events.query.fetch_objects(
            filters=wvc.query.Filter.by_property("dateLogged").greater_than(since_date),
            limit=limit
        )

        return [
            {
                "event_name": obj.properties.get("eventName"),
                "event_date": obj.properties.get("eventDate"),
                "event_type": obj.properties.get("eventType"),
                "event_url": obj.properties.get("eventUrl"),
                "description": obj.properties.get("description"),
                "ticket_price": obj.properties.get("ticketPrice"),
                "venue": obj.properties.get("venue"),
                "speakers": obj.properties.get("speakers"),
                "date_logged": obj.properties.get("dateLogged")
            }
            for obj in results.objects
        ]

