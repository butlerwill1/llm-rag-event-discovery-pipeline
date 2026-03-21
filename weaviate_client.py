"""
Weaviate vector database client for semantic event storage and retrieval.
"""

import os
import weaviate
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
from openai import OpenAI

logger = logging.getLogger(__name__)


class WeaviateEventStore:
    """Manages event storage and retrieval in Weaviate vector database."""
    
    def __init__(self, url: str = None):
        """
        Initialize Weaviate client.

        Args:
            url: Weaviate instance URL (defaults to env var WEAVIATE_URL)
        """
        self.url = url or os.getenv("WEAVIATE_URL", "http://localhost:8080")

        # Use Weaviate v3 client initialization (compatible with weaviate-client>=3.25.0)
        self.client = weaviate.Client(
            self.url,  # First positional argument is the URL
            additional_headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
        )
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create Event schema if it doesn't exist."""
        schema = {
            "class": "Event",
            "description": "London events found by AI agent",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-3-small",
                    "vectorizeClassName": False,
                    "vectorizePropertyName": False
                }
            },
            "properties": [
                {
                    "name": "eventName",
                    "dataType": ["text"],
                    "description": "Name of the event",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "eventDate",
                    "dataType": ["date"],
                    "description": "Date of the event"
                },
                {
                    "name": "eventType",
                    "dataType": ["text"],
                    "description": "Type/category of event"
                },
                {
                    "name": "eventUrl",
                    "dataType": ["text"],
                    "description": "URL to event page",
                    "tokenization": "field",  # Don't split URL
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True  # Don't vectorize URLs
                        }
                    }
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "Event description",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "ticketPrice",
                    "dataType": ["text"],
                    "description": "Ticket price information"
                },
                {
                    "name": "venue",
                    "dataType": ["text"],
                    "description": "Event venue/location"
                },
                {
                    "name": "speakers",
                    "dataType": ["text"],
                    "description": "Event speakers or organizers"
                },
                {
                    "name": "dateLogged",
                    "dataType": ["date"],
                    "description": "When this event was found by the agent"
                }
            ]
        }
        
        # Check if schema exists
        try:
            existing_schema = self.client.schema.get("Event")
            logger.info("Event schema already exists")
        except Exception:
            # Create schema
            self.client.schema.create_class(schema)
            logger.info("Created Event schema in Weaviate")
    
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
        data_object = {
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
        
        # Add to Weaviate
        uuid = self.client.data_object.create(
            data_object=data_object,
            class_name="Event"
        )
        
        logger.info(f"Added event to Weaviate: {event.get('event_name')} (UUID: {uuid})")
        return uuid

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
        url_results = (
            self.client.query
            .get("Event", ["eventName", "eventUrl"])
            .with_where({
                "path": ["eventUrl"],
                "operator": "Equal",
                "valueText": event.get("event_url", "")
            })
            .with_limit(1)
            .do()
        )

        if url_results.get("data", {}).get("Get", {}).get("Event"):
            logger.info(f"   ✓ Duplicate found (exact URL match)")
            return True

        # Method 2: RAG-powered LLM deduplication
        if use_llm:
            return self._is_duplicate_with_llm(event)
        else:
            # Fallback: Simple semantic similarity
            return self._is_duplicate_simple(event)

    def _is_duplicate_simple(self, event: Dict[str, Any], similarity_threshold: float = 0.95) -> bool:
        """Simple semantic similarity check without LLM."""
        search_text = f"{event.get('event_name', '')} {event.get('description', '')}"

        results = (
            self.client.query
            .get("Event", ["eventName", "eventUrl", "description"])
            .with_near_text({
                "concepts": [search_text],
                "certainty": similarity_threshold
            })
            .with_limit(1)
            .do()
        )

        similar_events = results.get("data", {}).get("Get", {}).get("Event", [])

        if similar_events:
            logger.info(f"✓ Duplicate found (semantic similarity): {event.get('event_name')} "
                       f"similar to {similar_events[0]['eventName']}")
            return True

        return False

    def _is_duplicate_with_llm(self, event: Dict[str, Any]) -> bool:
        """
        Use RAG + LLM to intelligently determine if event is duplicate.
        More accurate than simple similarity threshold.
        """
        # 1. Retrieve similar events (cast wider net with lower threshold)
        search_text = f"{event.get('event_name', '')} {event.get('description', '')}"

        logger.info(f"   🔎 Searching for similar events in database...")

        results = (
            self.client.query
            .get("Event", ["eventName", "eventDate", "eventUrl", "description", "venue", "eventType"])
            .with_near_text({
                "concepts": [search_text],
                "certainty": 0.85  # Lower threshold to catch more candidates
            })
            .with_limit(5)  # Get top 5 similar events
            .do()
        )

        similar_events = results.get("data", {}).get("Get", {}).get("Event", [])

        if not similar_events:
            logger.info(f"   ✗ No similar events found in database")
            return False

        logger.info(f"   📊 Found {len(similar_events)} similar event(s) in database")

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
        results = (
            self.client.query
            .get("Event", [
                "eventName", "eventDate", "eventType", "eventUrl",
                "description", "ticketPrice", "venue", "speakers", "dateLogged"
            ])
            .with_limit(limit)
            .do()
        )

        events = results.get("data", {}).get("Get", {}).get("Event", [])

        # Convert to standard format
        return [
            {
                "event_name": e.get("eventName"),
                "event_date": e.get("eventDate"),
                "event_type": e.get("eventType"),
                "event_url": e.get("eventUrl"),
                "description": e.get("description"),
                "ticket_price": e.get("ticketPrice"),
                "venue": e.get("venue"),
                "speakers": e.get("speakers"),
                "date_logged": e.get("dateLogged")
            }
            for e in events
        ]

    def search_events(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for events.

        Args:
            query: Natural language query
            limit: Maximum number of results

        Returns:
            List of matching events
        """
        results = (
            self.client.query
            .get("Event", [
                "eventName", "eventDate", "eventType", "eventUrl",
                "description", "ticketPrice", "venue", "speakers"
            ])
            .with_near_text({
                "concepts": [query]
            })
            .with_limit(limit)
            .do()
        )

        events = results.get("data", {}).get("Get", {}).get("Event", [])

        return [
            {
                "event_name": e.get("eventName"),
                "event_date": e.get("eventDate"),
                "event_type": e.get("eventType"),
                "event_url": e.get("eventUrl"),
                "description": e.get("description"),
                "ticket_price": e.get("ticketPrice"),
                "venue": e.get("venue"),
                "speakers": e.get("speakers")
            }
            for e in events
        ]

    def get_event_count(self) -> int:
        """Get total number of events in database."""
        result = (
            self.client.query
            .aggregate("Event")
            .with_meta_count()
            .do()
        )

        return result.get("data", {}).get("Aggregate", {}).get("Event", [{}])[0].get("meta", {}).get("count", 0)

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
            results = (
                self.client.query
                .get("Event", ["eventName", "eventDate"])
                .with_where({
                    "path": ["eventDate"],
                    "operator": "LessThan",
                    "valueDate": today
                })
                .with_limit(1000)  # Process in batches
                .do()
            )

            old_events = results.get("data", {}).get("Get", {}).get("Event", [])

            if not old_events:
                logger.info("No old events to clean up")
                return 0

            # Delete each old event
            deleted_count = 0
            for event in old_events:
                try:
                    # Get the UUID of the event
                    event_results = (
                        self.client.query
                        .get("Event", ["eventName", "eventDate"])
                        .with_where({
                            "path": ["eventName"],
                            "operator": "Equal",
                            "valueText": event.get("eventName", "")
                        })
                        .with_additional(["id"])
                        .with_limit(1)
                        .do()
                    )

                    events_with_id = event_results.get("data", {}).get("Get", {}).get("Event", [])

                    if events_with_id and "_additional" in events_with_id[0]:
                        event_id = events_with_id[0]["_additional"]["id"]
                        self.client.data_object.delete(event_id, "Event")
                        deleted_count += 1
                        logger.debug(f"Deleted: {event.get('eventName')} ({event.get('eventDate')})")

                except Exception as e:
                    logger.warning(f"Failed to delete event {event.get('eventName')}: {e}")
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
        results = (
            self.client.query
            .get("Event", [
                "eventName", "eventDate", "eventType", "eventUrl",
                "description", "ticketPrice", "venue", "speakers", "dateLogged"
            ])
            .with_where({
                "path": ["dateLogged"],
                "operator": "GreaterThan",
                "valueDate": since_date
            })
            .with_sort([{
                "path": ["dateLogged"],
                "order": "desc"
            }])
            .with_limit(limit)
            .do()
        )

        events = results.get("data", {}).get("Get", {}).get("Event", [])

        return [
            {
                "event_name": e.get("eventName"),
                "event_date": e.get("eventDate"),
                "event_type": e.get("eventType"),
                "event_url": e.get("eventUrl"),
                "description": e.get("description"),
                "ticket_price": e.get("ticketPrice"),
                "venue": e.get("venue"),
                "speakers": e.get("speakers"),
                "date_logged": e.get("dateLogged")
            }
            for e in events
        ]

