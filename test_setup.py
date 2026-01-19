#!/usr/bin/env python3
"""
Test script to verify the event finding AI agent setup
"""

import os
import sys
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import openai: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pandas: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import python-dotenv: {e}")
        return False
    
    return True


def test_local_modules():
    """Test that all local modules can be imported."""
    print("\nTesting local modules...")
    
    modules = [
        'config',
        'query_loader', 
        'event_parser',
        'memory',
        'openai_client'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            return False
    
    return True


def test_config():
    """Test configuration setup."""
    print("\nTesting configuration...")
    
    try:
        from config import OPENAI_API_KEY, QUERIES_FILE, EVENTS_LOG_FILE
        
        if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            print("✅ OpenAI API key is configured")
        else:
            print("⚠️  OpenAI API key not configured (check .env file)")
        
        print(f"✅ Queries file path: {QUERIES_FILE}")
        print(f"✅ Events log file path: {EVENTS_LOG_FILE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_file_operations():
    """Test file operations."""
    print("\nTesting file operations...")
    
    try:
        from query_loader import create_default_queries_file, load_queries
        from memory import initialize_events_log
        
        # Test query file creation
        create_default_queries_file()
        queries = load_queries()
        print(f"✅ Created and loaded {len(queries)} queries")
        
        # Test events log initialization
        initialize_events_log()
        print("✅ Events log initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations error: {e}")
        return False


def test_event_parsing():
    """Test event parsing functionality."""
    print("\nTesting event parsing...")
    
    try:
        from event_parser import parse_openai_response, validate_event, create_event_hash
        
        # Test with sample JSON
        sample_response = '''
        [
          {
            "event_name": "Test London Hackathon",
            "event_date": "2025-09-15",
            "event_type": "hackathon",
            "event_url": "https://example.com/test-hackathon"
          }
        ]
        '''
        
        events = parse_openai_response(sample_response)
        if events and len(events) == 1:
            print("✅ Event parsing successful")
            
            event = events[0]
            hash_value = create_event_hash(event)
            print(f"✅ Event hash created: {hash_value[:8]}...")
            
            return True
        else:
            print("❌ Event parsing failed")
            return False
            
    except Exception as e:
        print(f"❌ Event parsing error: {e}")
        return False


def test_memory_operations():
    """Test memory and deduplication functionality."""
    print("\nTesting memory operations...")
    
    try:
        from memory import log_new_events, is_duplicate_event, get_events_summary
        
        # Test with sample event
        test_event = {
            'event_name': 'Test Event',
            'event_date': '2025-12-01',
            'event_type': 'test',
            'event_url': 'https://example.com/test'
        }
        
        # Test logging
        logged_count = log_new_events([test_event])
        print(f"✅ Logged {logged_count} test event")
        
        # Test deduplication
        is_dup = is_duplicate_event(test_event)
        print(f"✅ Duplicate check: {is_dup} (should be True on second run)")
        
        # Test summary
        summary = get_events_summary()
        print(f"✅ Events summary: {summary['total_events']} total events")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory operations error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Event Finding AI Agent - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_local_modules,
        test_config,
        test_file_operations,
        test_event_parsing,
        test_memory_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("❌ Test failed")
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Set your OpenAI API key in .env file")
        print("2. Run: python main.py")
        print("3. Or try interactive mode: python main.py --interactive")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
