#!/usr/bin/env python3
"""
Personal Event Finding AI Agent

This script periodically searches for London-based events using OpenAI's Responses API
and logs new events to a CSV file while avoiding duplicates.
"""

import sys
import time
from typing import List, Dict, Any

from query_loader import load_queries, create_default_queries_file
from openai_client import EventSearchClient
from event_parser import parse_openai_response
from memory import initialize_events_log, log_new_events, get_events_summary, search_events
from email_service import create_email_service_from_env
from config import QUERIES_FILE, EVENTS_LOG_FILE


def main():
    """Main function that orchestrates the event finding process."""
    print("🤖 Personal Event Finding AI Agent")
    print("=" * 50)
    
    # Initialize components
    print("Initializing...")
    initialize_events_log()
    
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
    
    # Log new events
    print(f"\n💾 Processing {len(all_new_events)} total events...")
    if all_new_events:
        new_count = log_new_events(all_new_events)
        print(f"Logged {new_count} new events (skipped {len(all_new_events) - new_count} duplicates)")
    else:
        print("No events to log")
    
    # Show summary
    print(f"\n Events Summary:")
    summary = get_events_summary()
    print(f"Total events in database: {summary['total_events']}")
    
    if summary['event_types']:
        print("Event types:")
        for event_type, count in summary['event_types'].items():
            print(f"  • {event_type}: {count}")
    
    if summary['recent_events']:
        print("\nMost recent events:")
        for event in summary['recent_events'][:3]:
            print(f"  • {event['event_name']} ({event['event_type']}) - {event['event_date']}")
    
    print(f"\n✅ Event search completed! Check {EVENTS_LOG_FILE} for all events.")

    # Send email digest
    print(f"\n📧 Sending email digest...")
    try:
        email_service = create_email_service_from_env()
        email_sent = email_service.send_weekly_digest(all_new_events, summary['total_events'])

        if not email_sent:
            print("⚠️  Email was not sent. Check the error messages above.")
    except ValueError as e:
        print(f"⚠️  Email service not configured: {e}")
        print("   Set SES_FROM_EMAIL in your .env file to enable email notifications")
    except Exception as e:
        print(f"⚠️  Failed to send email: {e}")


def interactive_mode():
    """Interactive mode for managing queries and searching events."""
    print("🔍 Interactive Event Search Mode")
    print("Commands: search, add, remove, list, summary, quit")
    
    client = EventSearchClient()
    
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
                                new_count = log_new_events(events)
                                print(f"Saved {new_count} new events")
                        else:
                            print("No events found")
                    else:
                        print("No response received")
            
            elif command == "add":
                query = input("Enter new search query: ").strip()
                if query:
                    from query_loader import add_query
                    add_query(query)
            
            elif command == "list":
                queries = load_queries()
                print(f"Current queries ({len(queries)}):")
                for i, query in enumerate(queries, 1):
                    print(f"  {i}. {query}")
            
            elif command == "summary":
                summary = get_events_summary()
                print(f"Total events: {summary['total_events']}")
                print(f"Event types: {summary['event_types']}")
            
            elif command == "find":
                search_term = input("Search events for: ").strip()
                if search_term:
                    results = search_events(search_term)
                    print(f"Found {len(results)} matching events:")
                    for event in results[:10]:  # Show first 10
                        print(f"  • {event['event_name']} - {event['event_date']}")
            
            else:
                print("Unknown command. Available: search, add, list, summary, find, quit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()
