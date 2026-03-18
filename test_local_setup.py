#!/usr/bin/env python3
"""
Quick test script to verify local setup is working correctly.
Run this before running the full pipeline.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_variables():
    """Test that required environment variables are set."""
    print("\n🔍 Testing Environment Variables...")
    
    required = {
        'OPENAI_API_KEY': 'Required for event search and embeddings',
    }
    
    optional = {
        'SES_FROM_EMAIL': 'Required for sending emails',
        'SES_TO_EMAIL': 'Required for sending emails',
        'AWS_REGION': 'Required for AWS SES',
        'MODEL_NAME': 'Defaults to gpt-4o',
        'WEAVIATE_URL': 'Defaults to http://localhost:8080',
    }
    
    all_good = True
    
    # Check required
    for var, description in required.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:20]}... ({description})")
        else:
            print(f"  ❌ {var}: NOT SET - {description}")
            all_good = False
    
    # Check optional
    for var, description in optional.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value} ({description})")
        else:
            print(f"  ⚠️  {var}: NOT SET - {description}")
    
    return all_good


def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🤖 Testing OpenAI Connection...")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("  ❌ OPENAI_API_KEY not set")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Say "test successful"'}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"  ✅ OpenAI API works! Response: {result}")
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI connection failed: {e}")
        return False


def test_weaviate_connection():
    """Test Weaviate connection."""
    print("\n🗄️  Testing Weaviate Connection...")
    
    try:
        import weaviate
        
        weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        print(f"  Connecting to: {weaviate_url}")
        
        client = weaviate.Client(weaviate_url)
        
        # Test connection
        schema = client.schema.get()
        print(f"  ✅ Weaviate connection works!")
        
        # Check if Event class exists
        classes = [c['class'] for c in schema.get('classes', [])]
        if 'Event' in classes:
            print(f"  ✅ Event schema exists")
            
            # Get event count
            result = client.query.aggregate("Event").with_meta_count().do()
            count = result['data']['Aggregate']['Event'][0]['meta']['count']
            print(f"  📊 Current events in database: {count}")
        else:
            print(f"  ⚠️  Event schema not found (will be created on first run)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Weaviate connection failed: {e}")
        print(f"  💡 Make sure Weaviate is running: docker-compose up -d weaviate")
        return False


def test_queries_file():
    """Test that queries.txt exists and has content."""
    print("\n📝 Testing Queries File...")
    
    try:
        with open('queries.txt', 'r') as f:
            queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if queries:
            print(f"  ✅ Found {len(queries)} queries:")
            for i, query in enumerate(queries[:3], 1):
                print(f"     {i}. {query}")
            if len(queries) > 3:
                print(f"     ... and {len(queries) - 3} more")
            return True
        else:
            print(f"  ⚠️  queries.txt is empty")
            return False
            
    except FileNotFoundError:
        print(f"  ❌ queries.txt not found")
        return False


def test_aws_credentials():
    """Test AWS credentials (optional)."""
    print("\n☁️  Testing AWS Credentials (Optional)...")
    
    try:
        import boto3
        
        # Try to create SES client
        region = os.getenv('AWS_REGION', 'eu-west-1')
        ses_client = boto3.client('ses', region_name=region)
        
        # Try to get send quota (doesn't send email, just checks access)
        quota = ses_client.get_send_quota()
        print(f"  ✅ AWS SES access works!")
        print(f"     Region: {region}")
        print(f"     Daily quota: {quota['Max24HourSend']}")
        print(f"     Sent today: {quota['SentLast24Hours']}")
        return True
        
    except Exception as e:
        print(f"  ⚠️  AWS credentials not configured: {e}")
        print(f"  💡 This is OK for testing - email sending will be skipped")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Local Setup Test Suite")
    print("=" * 60)
    
    results = {
        'Environment Variables': test_env_variables(),
        'OpenAI Connection': test_openai_connection(),
        'Weaviate Connection': test_weaviate_connection(),
        'Queries File': test_queries_file(),
        'AWS Credentials': test_aws_credentials(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    # Determine overall status
    critical_tests = ['Environment Variables', 'OpenAI Connection', 'Weaviate Connection', 'Queries File']
    critical_passed = all(results[test] for test in critical_tests)
    
    print("\n" + "=" * 60)
    if critical_passed:
        print("🎉 All critical tests passed! You're ready to run the pipeline.")
        print("\nNext steps:")
        print("  1. Run the full pipeline: python main.py")
        print("  2. Or use Docker: docker-compose up")
        print("  3. Check the results in Weaviate")
        return 0
    else:
        print("⚠️  Some critical tests failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("  1. Make sure .env file has OPENAI_API_KEY")
        print("  2. Start Weaviate: docker-compose up -d weaviate")
        print("  3. Check queries.txt exists and has queries")
        return 1


if __name__ == '__main__':
    sys.exit(main())

