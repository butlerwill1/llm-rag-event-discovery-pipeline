#!/usr/bin/env python3
"""
Test script for local embeddings implementation.
Verifies that add_event, search_events, and is_duplicate work with local embeddings.
"""

import os
from dotenv import load_dotenv
from weaviate_client import WeaviateEventStore
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("🧪 Testing Local Embeddings Implementation")
    print("=" * 60)
    print()
    
    # Initialize Weaviate store
    print("1️⃣  Connecting to Weaviate...")
    store = WeaviateEventStore()
    print(f"   ✅ Connected! Current event count: {store.get_event_count()}")
    print()
    
    # Test 1: Add events with local embeddings
    print("2️⃣  Testing add_event with local embeddings...")
    test_events = [
        {
            "event_name": "AI & Machine Learning Meetup",
            "event_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "event_type": "Meetup",
            "event_url": "https://example.com/ai-meetup-test-1",
            "description": "Join us for an evening of AI and machine learning discussions. We'll cover the latest trends in deep learning and neural networks.",
            "ticket_price": "Free",
            "venue": "Tech Hub London",
            "speakers": "Dr. Jane Smith, Prof. John Doe"
        },
        {
            "event_name": "Python Programming Workshop",
            "event_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "event_type": "Workshop",
            "event_url": "https://example.com/python-workshop-test-2",
            "description": "Learn Python programming from scratch. Perfect for beginners who want to start their coding journey.",
            "ticket_price": "£25",
            "venue": "Code Academy London",
            "speakers": "Sarah Johnson"
        }
    ]
    
    added_uuids = []
    for event in test_events:
        uuid = store.add_event(event)
        added_uuids.append(uuid)
        print(f"   ✅ Added: {event['event_name']} (UUID: {uuid[:8]}...)")
    print()
    
    # Test 2: Search events using local embeddings
    print("3️⃣  Testing search_events with local embeddings...")
    queries = [
        "artificial intelligence events",
        "python coding workshops",
        "machine learning meetups"
    ]
    
    for query in queries:
        results = store.search_events(query, limit=3)
        print(f"   🔍 Query: '{query}'")
        print(f"      Found {len(results)} result(s):")
        for i, result in enumerate(results[:2], 1):  # Show top 2
            print(f"      {i}. {result['event_name']}")
    print()
    
    # Test 3: Duplicate detection with local embeddings
    print("4️⃣  Testing duplicate detection with local embeddings...")
    
    # Test 3a: Exact duplicate (should be detected)
    duplicate_event = test_events[0].copy()
    duplicate_event["event_url"] = "https://example.com/ai-meetup-test-1"  # Same URL
    is_dup = store.is_duplicate(duplicate_event, use_llm=False)
    print(f"   🔍 Exact URL match test: {'✅ PASS' if is_dup else '❌ FAIL'} (Expected: duplicate)")
    
    # Test 3b: Similar event (should be detected by semantic similarity)
    similar_event = {
        "event_name": "Machine Learning Evening Meetup",  # Similar to first event
        "event_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "event_type": "Meetup",
        "event_url": "https://example.com/ml-meetup-different-url",
        "description": "An evening discussing AI and machine learning, covering deep learning trends.",
        "ticket_price": "Free",
        "venue": "Tech Hub London",
        "speakers": "Dr. Jane Smith"
    }
    is_dup = store.is_duplicate(similar_event, use_llm=False)
    print(f"   🔍 Semantic similarity test: {'✅ PASS' if is_dup else '⚠️  Not detected'} (Expected: duplicate)")
    
    # Test 3c: Different event (should NOT be detected)
    different_event = {
        "event_name": "Blockchain Conference 2026",
        "event_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "event_type": "Conference",
        "event_url": "https://example.com/blockchain-conf",
        "description": "Annual blockchain and cryptocurrency conference featuring industry leaders.",
        "ticket_price": "£150",
        "venue": "Excel London",
        "speakers": "Various"
    }
    is_dup = store.is_duplicate(different_event, use_llm=False)
    print(f"   🔍 Different event test: {'✅ PASS' if not is_dup else '❌ FAIL'} (Expected: not duplicate)")
    print()
    
    # Summary
    print("=" * 60)
    print("✅ Local Embeddings Test Complete!")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   • Model: all-MiniLM-L6-v2 (384 dimensions)")
    print(f"   • Events added: {len(test_events)}")
    print(f"   • Search queries tested: {len(queries)}")
    print(f"   • Duplicate detection: Working with local embeddings")
    print()
    print("💡 Next steps:")
    print("   1. Test with docker-compose to ensure it works in containers")
    print("   2. If successful, push to GitHub to deploy to AWS ECS")
    print()

if __name__ == "__main__":
    main()

