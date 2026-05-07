#!/usr/bin/env python3
"""
LLM RAG Event Discovery Pipeline

This script periodically searches for London-based events using OpenAI's Responses API
and logs new events to a Weaviate Vector Database.
"""

import sys
import time

from .query_loader import load_queries, create_default_queries_file
from .openai_client import EventSearchClient
from .event_parser import parse_openai_response
from .weaviate_client import WeaviateEventStore
from .email_service import create_email_service_from_env
from .config import QUERIES_FILE
from datetime import datetime
import logging

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simple format for clean output
)

logger = logging.getLogger(__name__)


def main():
    """Main function that orchestrates the event finding process."""
    print("🤖 LLM RAG Event Discovery Pipeline")
    print("=" * 50)

    # Initialize Weaviate store
    print("Initializing Weaviate...")
    weaviate_store = None
    try:
        weaviate_store = WeaviateEventStore()
        print("✅ Connected to Weaviate")
    except Exception as e:
        print(f"❌ Failed to connect to Weaviate: {e}")
        print("Make sure Weaviate is running: docker-compose up -d weaviate")
        return

    try:
        # Load queries
        queries = load_queries()
        if not queries:
            print(f"No queries found in {QUERIES_FILE}")
            print("Creating default queries file...")
            create_default_queries_file()
            queries = load_queries()

        print(f"Loaded {len(queries)} search queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")

        # Initialize OpenAI client
        print("\nInitializing OpenAI client...")
        client = EventSearchClient()

        # Test connection
        if not client.test_connection():
            print("Failed to connect to OpenAI API. Please check your API key.")
            return

        print("OpenAI connection successful!")

        # Process each query
        print(f"\nSearching for events...")
        all_new_events = []

        for i, query in enumerate(queries, 1):
            print(f"\n📍 Query {i}/{len(queries)}: {query}")
            print("-" * 40)

            try:
                # Search for events
                response = client.search_events(query)

                if response:
                    # Parse the response
                    events = parse_openai_response(response)

                    if events:
                        print(f"Found {len(events)} events:")
                        for event in events:
                            print(f"  • {event['event_name']} ({event['event_type']}) - {event['event_date']}")
                            print(f"    Price: {event.get('ticket_price', 'N/A')} | Venue: {event.get('venue', 'N/A')}")
                            if event.get('description'):
                                desc = event['description'][:100] + "..." if len(event['description']) > 100 else event['description']
                                print(f"    Description: {desc}")

                        all_new_events.extend(events)
                    else:
                        print("No valid events found in response")
                else:
                    print("No response received")

            except Exception as e:
                print(f"Error processing query: {e}")
                continue

            # Add a delay between requests to avoid rate limits
            if i < len(queries):
                print(f"Waiting 10 seconds before next query to avoid rate limits...")
                time.sleep(10)

        # Clean up old events first (to save costs on deduplication checks)
        print(f"\n🧹 Cleaning up past events...")
        deleted_count = weaviate_store.cleanup_past_events()
        if deleted_count > 0:
            print(f"   Removed {deleted_count} events that already occurred")

        # Process and add new events
        print(f"\n💾 Processing {len(all_new_events)} total events...")

        # Get current database stats
        total_in_db = weaviate_store.get_event_count()
        print(f"   Current events in database: {total_in_db}")

        newly_added_events = []
        new_count = 0
        skipped_past = 0

        if all_new_events:
            current_timestamp = datetime.now().isoformat()
            today = datetime.now().date()

            print(f"\n🔍 Starting deduplication process...")
            print(f"   Checking each event against {total_in_db} existing events\n")

            for event in all_new_events:
                # Filter out past events
                event_date_str = event.get('event_date', '')
                if event_date_str:
                    try:
                        # Parse the event date
                        if 'T' in event_date_str:
                            event_date = datetime.fromisoformat(event_date_str.replace('Z', '')).date()
                        else:
                            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

                        # Skip if event is in the past
                        if event_date < today:
                            print(f"  ⏭️  Skipped past event: {event['event_name']} ({event_date_str})")
                            skipped_past += 1
                            continue
                    except Exception as e:
                        logger.warning(f"Could not parse date for {event['event_name']}: {event_date_str}")
                        # Continue processing if date parsing fails

                # Check if duplicate using RAG-powered deduplication
                if not weaviate_store.is_duplicate(event):
                    # Add timestamp
                    event['date_logged'] = current_timestamp

                    # Add to Weaviate
                    try:
                        weaviate_store.add_event(event)
                        newly_added_events.append(event)
                        new_count += 1
                        print(f"  ✅ Added: {event['event_name']}")
                    except Exception as e:
                        logger.error(f"Failed to add event {event['event_name']}: {e}")
                else:
                    print(f"  ⏭️  Skipped duplicate: {event['event_name']}")

            duplicates_skipped = len(all_new_events) - new_count - skipped_past
            print(f"\n✅ Logged {new_count} new events")
            if skipped_past > 0:
                print(f"   ⏭️  Skipped {skipped_past} past events")
            if duplicates_skipped > 0:
                print(f"   ⏭️  Skipped {duplicates_skipped} duplicates")
        else:
            print("No events to log")

        # Show summary
        print(f"\n📊 Events Summary:")
        total_events = weaviate_store.get_event_count()
        print(f"Total events in database: {total_events}")

        all_events = weaviate_store.get_all_events(limit=100)
        if all_events:
            # Count event types
            event_types = {}
            for event in all_events:
                event_type = event.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1

            if event_types:
                print("Event types:")
                for event_type, count in event_types.items():
                    print(f"  • {event_type}: {count}")

            # Show recent events
            recent_events = sorted(all_events, key=lambda x: x.get('date_logged', ''), reverse=True)[:3]
            if recent_events:
                print("\nMost recent events:")
                for event in recent_events:
                    print(f"  • {event['event_name']} ({event['event_type']}) - {event['event_date']}")

        print(f"\n✅ Event search completed! Events stored in Weaviate vector database.")

        # Send email digest with ONLY the newly added events (not all searched events)
        print(f"\n📧 Sending email digest...")
        try:
            email_service = create_email_service_from_env()
            # Send only the events that were actually added (after deduplication)
            email_sent = email_service.send_weekly_digest(newly_added_events, total_events)

            if not email_sent:
                print("⚠️  Email was not sent. Check the error messages above.")
        except ValueError as e:
            print(f"⚠️  Email service not configured: {e}")
            print("   Set SES_FROM_EMAIL in your .env file to enable email notifications")
        except Exception as e:
            print(f"⚠️  Failed to send email: {e}")

    finally:
        # Clean up Weaviate connection
        if weaviate_store is not None:
            try:
                weaviate_store.client.close()
                logger.info("✅ Weaviate connection closed")
            except Exception as e:
                logger.warning(f"Error closing Weaviate connection: {e}")


def interactive_mode():
    """Interactive mode for managing queries and searching events."""
    print("Interactive Event Discovery Mode")
    print("Commands: search, add, remove, list, summary, find, quit")

    client = EventSearchClient()

    # Initialize Weaviate
    weaviate_store = None
    try:
        weaviate_store = WeaviateEventStore()
    except Exception as e:
        print(f"❌ Failed to connect to Weaviate: {e}")
        return

    try:
        while True:
            try:
                command = input("\n> ").strip().lower()

                if command == "quit" or command == "exit":
                    break
                elif command == "search":
                    query = input("Enter search query: ").strip()
                    if query:
                        response = client.search_events(query)
                        if response:
                            events = parse_openai_response(response)
                            if events:
                                print(f"Found {len(events)} events:")
                                for i, event in enumerate(events, 1):
                                    print(f"\n  {i}. {event['event_name']} - {event['event_date']}")
                                    print(f"     Type: {event['event_type']} | Price: {event.get('ticket_price', 'N/A')}")
                                    print(f"     Venue: {event.get('venue', 'N/A')}")
                                    if event.get('speakers') and event['speakers'] != 'Speakers TBA':
                                        print(f"     Speakers: {event['speakers']}")
                                    if event.get('description'):
                                        desc = event['description'][:150] + "..." if len(event['description']) > 150 else event['description']
                                        print(f"     Description: {desc}")
                                    print(f"     URL: {event['event_url']}")

                                save = input("\nSave these events? (y/n): ").strip().lower()
                                if save == 'y':
                                    new_count = 0
                                    for event in events:
                                        if not weaviate_store.is_duplicate(event):
                                            event['date_logged'] = datetime.now().isoformat()
                                            weaviate_store.add_event(event)
                                            new_count += 1
                                    print(f"Saved {new_count} new events")
                            else:
                                print("No events found")
                        else:
                            print("No response received")

                elif command == "add":
                    query = input("Enter new search query: ").strip()
                    if query:
                        from .query_loader import add_query
                        add_query(query)

                elif command == "list":
                    queries = load_queries()
                    print(f"Current queries ({len(queries)}):")
                    for i, query in enumerate(queries, 1):
                        print(f"  {i}. {query}")

                elif command == "summary":
                    total = weaviate_store.get_event_count()
                    print(f"Total events: {total}")

                    all_events = weaviate_store.get_all_events(limit=100)
                    if all_events:
                        event_types = {}
                        for event in all_events:
                            event_type = event.get('event_type', 'unknown')
                            event_types[event_type] = event_types.get(event_type, 0) + 1
                        print(f"Event types: {event_types}")

                elif command == "find":
                    search_term = input("Search events for: ").strip()
                    if search_term:
                        results = weaviate_store.search_events(search_term, limit=10)
                        print(f"Found {len(results)} matching events:")
                        for event in results:
                            print(f"  • {event['event_name']} - {event['event_date']}")

                else:
                    print("Unknown command. Available: search, add, list, summary, find, quit")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    finally:
        # Clean up Weaviate connection
        if weaviate_store is not None:
            try:
                weaviate_store.client.close()
                logger.info("✅ Weaviate connection closed (interactive mode)")
            except Exception as e:
                logger.warning(f"Error closing Weaviate connection: {e}")

    print("Goodbye!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()
