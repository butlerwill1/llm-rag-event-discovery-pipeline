"""
Module for managing event memory and deduplication
"""
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Set
from config import EVENTS_LOG_FILE, CSV_COLUMNS
from event_parser import create_event_hash


def initialize_events_log():
    """
    Initialize the events log CSV file if it doesn't exist.
    """
    if not os.path.exists(EVENTS_LOG_FILE):
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(EVENTS_LOG_FILE, index=False)
        print(f"Created new events log file: {EVENTS_LOG_FILE}")


def load_existing_events() -> pd.DataFrame:
    """
    Load existing events from the CSV file.
    
    Returns:
        pd.DataFrame: DataFrame containing existing events
    """
    try:
        if os.path.exists(EVENTS_LOG_FILE):
            df = pd.read_csv(EVENTS_LOG_FILE)
            return df
        else:
            initialize_events_log()
            return pd.DataFrame(columns=CSV_COLUMNS)
    except Exception as e:
        print(f"Error loading events log: {e}")
        return pd.DataFrame(columns=CSV_COLUMNS)


def get_existing_event_hashes() -> Set[str]:
    """
    Get a set of hashes for all existing events for quick deduplication.
    
    Returns:
        Set[str]: Set of event hashes
    """
    df = load_existing_events()
    hashes = set()
    
    for _, row in df.iterrows():
        try:
            event = {
                'event_name': row['event_name'],
                'event_date': row['event_date']
            }
            hash_value = create_event_hash(event)
            hashes.add(hash_value)
        except Exception as e:
            print(f"Error creating hash for existing event: {e}")
            continue
    
    return hashes


def get_existing_urls() -> Set[str]:
    """
    Get a set of URLs for all existing events for URL-based deduplication.
    
    Returns:
        Set[str]: Set of event URLs
    """
    df = load_existing_events()
    if 'event_url' in df.columns:
        return set(df['event_url'].dropna().tolist())
    return set()


def is_duplicate_event(event: Dict[str, Any]) -> bool:
    """
    Check if an event is a duplicate based on hash and URL.
    
    Args:
        event (Dict[str, Any]): Event to check
        
    Returns:
        bool: True if event is a duplicate, False otherwise
    """
    # Check by hash (name + date)
    event_hash = create_event_hash(event)
    existing_hashes = get_existing_event_hashes()
    
    if event_hash in existing_hashes:
        return True
    
    # Check by URL
    existing_urls = get_existing_urls()
    if event['event_url'] in existing_urls:
        return True
    
    return False


def log_new_events(events: List[Dict[str, Any]]) -> int:
    """
    Log new events to the CSV file, skipping duplicates.
    
    Args:
        events (List[Dict[str, Any]]): List of events to log
        
    Returns:
        int: Number of new events logged
    """
    if not events:
        return 0
    
    new_events = []
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for event in events:
        if not is_duplicate_event(event):
            # Add timestamp
            event_with_timestamp = event.copy()
            event_with_timestamp['date_logged'] = current_timestamp
            new_events.append(event_with_timestamp)
        else:
            print(f"Skipping duplicate event: {event['event_name']}")
    
    if new_events:
        # Load existing data
        df_existing = load_existing_events()
        
        # Create DataFrame for new events
        df_new = pd.DataFrame(new_events)
        
        # Combine and save
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(EVENTS_LOG_FILE, index=False)
        
        print(f"Logged {len(new_events)} new events to {EVENTS_LOG_FILE}")
        
        # Print summary of new events
        for event in new_events:
            print(f"  - {event['event_name']} ({event['event_type']}) on {event['event_date']}")
    
    return len(new_events)


def get_events_summary() -> Dict[str, Any]:
    """
    Get a summary of all logged events.
    
    Returns:
        Dict[str, Any]: Summary statistics
    """
    df = load_existing_events()
    
    if df.empty:
        return {
            'total_events': 0,
            'event_types': {},
            'recent_events': []
        }
    
    summary = {
        'total_events': len(df),
        'event_types': df['event_type'].value_counts().to_dict() if 'event_type' in df.columns else {},
        'recent_events': []
    }
    
    # Get 5 most recent events
    if 'date_logged' in df.columns:
        df_sorted = df.sort_values('date_logged', ascending=False)
        recent = df_sorted.head(5)
        summary['recent_events'] = recent[['event_name', 'event_date', 'event_type']].to_dict('records')
    
    return summary


def search_events(query: str) -> List[Dict[str, Any]]:
    """
    Search for events in the log that match a query.
    
    Args:
        query (str): Search query
        
    Returns:
        List[Dict[str, Any]]: Matching events
    """
    df = load_existing_events()
    
    if df.empty:
        return []
    
    # Search in event name and type
    query_lower = query.lower()
    mask = (
        df['event_name'].str.lower().str.contains(query_lower, na=False) |
        df['event_type'].str.lower().str.contains(query_lower, na=False)
    )
    
    matching_events = df[mask].to_dict('records')
    return matching_events


if __name__ == "__main__":
    # Test the module
    initialize_events_log()
    
    # Test with sample events
    test_events = [
        {
            'event_name': 'Test Hackathon',
            'event_date': '2025-09-15',
            'event_type': 'hackathon',
            'event_url': 'https://example.com/test'
        }
    ]
    
    logged_count = log_new_events(test_events)
    print(f"Logged {logged_count} test events")
    
    summary = get_events_summary()
    print(f"Total events in log: {summary['total_events']}")
    print(f"Event types: {summary['event_types']}")
