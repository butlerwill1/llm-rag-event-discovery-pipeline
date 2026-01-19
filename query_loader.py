"""
Module for loading and managing search queries
"""
import os
from datetime import datetime, timedelta
from typing import List
from config import QUERIES_FILE


def load_queries() -> List[str]:
    """
    Load search queries from the queries file and enhance them for future event searching.

    Returns:
        List[str]: List of enhanced search queries, one per line
    """
    if not os.path.exists(QUERIES_FILE):
        print(f"Warning: {QUERIES_FILE} not found. Creating empty file.")
        create_default_queries_file()
        return []

    try:
        with open(QUERIES_FILE, 'r', encoding='utf-8') as file:
            queries = [line.strip() for line in file.readlines()]
            # Filter out empty lines and comments (lines starting with #)
            queries = [q for q in queries if q and not q.startswith('#')]

            # Enhance queries to be future-focused
            enhanced_queries = []
            for query in queries:
                enhanced_query = enhance_query_for_future_events(query)
                enhanced_queries.append(enhanced_query)

            return enhanced_queries
    except Exception as e:
        print(f"Error reading {QUERIES_FILE}: {e}")
        return []


def enhance_query_for_future_events(query: str) -> str:
    """
    Enhance a query to focus on upcoming/future events.
    For marathon events, adds specific future date terms (at least 2 months ahead).
    For other events, adds "upcoming" prefix.

    Args:
        query (str): Original query

    Returns:
        str: Enhanced query focused on future events
    """
    # Don't modify if already contains future-focused terms
    future_terms = ['upcoming', 'future', '2025', '2026', 'next', 'coming']
    if any(term in query.lower() for term in future_terms):
        return query

    query_lower = query.lower()

    # Special handling for marathon events - need at least 2 months advance notice
    if any(marathon_term in query_lower for marathon_term in ['marathon', 'half marathon', 'half-marathon', '10k', '5k', 'run', 'running']):
        return enhance_marathon_query(query)

    # For other events, just add "upcoming"
    enhanced = f"upcoming {query}"
    return enhanced


def enhance_marathon_query(query: str) -> str:
    """
    Enhance marathon/running event queries with specific future date terms.
    Ensures events are at least 2 months in the future.

    Args:
        query (str): Original marathon query

    Returns:
        str: Enhanced query with future date terms
    """
    current_date = datetime.now()
    # Calculate 2 months ahead
    future_date = current_date + timedelta(days=60)  # Approximately 2 months

    current_year = current_date.year
    future_year = future_date.year
    future_month = future_date.month

    # Month names for natural language
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    future_month_name = month_names[future_month - 1]

    # Create enhanced query with specific future terms
    if future_year > current_year:
        # If we're looking into next year
        enhanced = f"{query} {future_year}"
    else:
        # Same year, add month and year
        enhanced = f"{query} {future_month_name} {future_year}"

    return enhanced


def create_default_queries_file():
    """
    Create a default queries.txt file with sample queries.
    """
    default_queries = [
        "# Event search queries - one per line",
        "# Lines starting with # are comments and will be ignored",
        "# The system automatically searches for upcoming/future events",
        "# Marathon events automatically get 2+ months advance notice",
        "",
        "London hackathon",
        "Half marathon London",
        "London marathon",
        "10k run London",
        "Climate networking London",
        "Product design conference London",
        "Tech meetup London",
        "Startup networking event London",
        "AI conference London",
        "Web3 blockchain event London",
        "Data science meetup London",
        "UX design workshop London",
        "Fintech conference London"
    ]
    
    try:
        with open(QUERIES_FILE, 'w', encoding='utf-8') as file:
            file.write('\n'.join(default_queries))
        print(f"Created default {QUERIES_FILE} with sample queries.")
    except Exception as e:
        print(f"Error creating {QUERIES_FILE}: {e}")


def add_query(query: str):
    """
    Add a new query to the queries file.
    
    Args:
        query (str): The search query to add
    """
    try:
        with open(QUERIES_FILE, 'a', encoding='utf-8') as file:
            file.write(f"\n{query}")
        print(f"Added query: {query}")
    except Exception as e:
        print(f"Error adding query: {e}")


def remove_query(query: str):
    """
    Remove a query from the queries file.
    
    Args:
        query (str): The search query to remove
    """
    try:
        queries = load_queries()
        if query in queries:
            queries.remove(query)
            
            # Rewrite the file
            with open(QUERIES_FILE, 'w', encoding='utf-8') as file:
                file.write("# Event search queries - one per line\n")
                file.write("# Lines starting with # are comments and will be ignored\n\n")
                for q in queries:
                    file.write(f"{q}\n")
            print(f"Removed query: {query}")
        else:
            print(f"Query not found: {query}")
    except Exception as e:
        print(f"Error removing query: {e}")


if __name__ == "__main__":
    # Test the module
    print("Testing query enhancement:")

    test_queries = [
        "London hackathon",
        "Half marathon London",
        "Tech meetup London",
        "London marathon",
        "10k run London"
    ]

    for query in test_queries:
        enhanced = enhance_query_for_future_events(query)
        print(f"Original: '{query}' -> Enhanced: '{enhanced}'")

    print(f"\nLoading actual queries:")
    queries = load_queries()
    print(f"Loaded {len(queries)} enhanced queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
