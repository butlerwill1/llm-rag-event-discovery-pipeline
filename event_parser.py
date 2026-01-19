"""
Module for parsing OpenAI responses and extracting event data
"""
import json
import re
from typing import List, Dict, Any
from datetime import datetime


def parse_openai_response(response_content: str) -> List[Dict[str, Any]]:
    """Parse OpenAI response and extract structured event data.
    
    Args:
        response_content (str): Raw response content from OpenAI
        
    Returns:
        List[Dict[str, Any]]: List of parsed event dictionaries
    """
    events = []
    
    try:
        # Try to extract JSON from the response
        json_content = extract_json_from_text(response_content)
        
        if json_content:
            # Parse the JSON
            parsed_data = json.loads(json_content)
            
            # Handle both single objects and arrays
            if isinstance(parsed_data, list):
                events = parsed_data
            elif isinstance(parsed_data, dict):
                events = [parsed_data]
            
            # Validate and clean each event
            validated_events = []
            for event in events:
                validated_event = validate_event(event)
                if validated_event:
                    validated_events.append(validated_event)
            
            return validated_events
            
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response content: {response_content[:500]}...")
    except Exception as e:
        print(f"Error parsing response: {e}")
    
    return []


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON content from text that might contain other content.
    
    Args:
        text (str): Text that may contain JSON
        
    Returns:
        str: Extracted JSON string or empty string if not found
    """
    # Look for JSON array or object patterns
    json_patterns = [
        r'\[.*?\]',  # Array pattern
        r'\{.*?\}',  # Object pattern
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # Test if it's valid JSON
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
    
    # If no valid JSON found, try to clean the text
    cleaned_text = text.strip()
    if cleaned_text.startswith('```json'):
        cleaned_text = cleaned_text[7:]
    if cleaned_text.endswith('```'):
        cleaned_text = cleaned_text[:-3]
    
    return cleaned_text.strip()


def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean event data.

    Args:
        event (Dict[str, Any]): Raw event dictionary

    Returns:
        Dict[str, Any]: Validated event dictionary or None if invalid
    """
    required_fields = ["event_name", "event_date", "event_type", "event_url"]

    # Check if all required fields are present
    for field in required_fields:
        if field not in event or not event[field]:
            print(f"Missing or empty required field: {field}")
            return None

    # Clean and validate the data
    validated_event = {}

    # Event name
    validated_event["event_name"] = str(event["event_name"]).strip()

    # Event date - try to parse and standardize
    validated_event["event_date"] = parse_event_date(event["event_date"])
    if not validated_event["event_date"]:
        print(f"Invalid date format: {event['event_date']}")
        return None

    # Event type
    validated_event["event_type"] = str(event["event_type"]).strip().lower()

    # Event URL - basic validation
    event_url = str(event["event_url"]).strip()
    if not (event_url.startswith("http://") or event_url.startswith("https://")):
        print(f"Invalid URL format: {event_url}")
        return None
    validated_event["event_url"] = event_url

    # Handle optional fields with defaults
    validated_event["description"] = clean_text_field(event.get("description", "No description available"))
    validated_event["ticket_price"] = clean_text_field(event.get("ticket_price", "Price not specified"))
    validated_event["venue"] = clean_text_field(event.get("venue", "Venue TBA"))
    validated_event["speakers"] = clean_text_field(event.get("speakers", "Speakers TBA"))

    return validated_event


def clean_text_field(text: Any) -> str:
    """
    Clean and validate text fields.

    Args:
        text (Any): Text to clean

    Returns:
        str: Cleaned text
    """
    if not text or text in [None, "null", "None"]:
        return "Not specified"

    cleaned = str(text).strip()

    # Remove excessive whitespace
    cleaned = " ".join(cleaned.split())

    # Limit length to prevent CSV issues
    if len(cleaned) > 500:
        cleaned = cleaned[:497] + "..."

    return cleaned if cleaned else "Not specified"


def parse_event_date(date_str: str) -> str:
    """
    Parse various date formats and return standardized ISO format.
    
    Args:
        date_str (str): Date string in various formats
        
    Returns:
        str: ISO formatted date string (YYYY-MM-DD) or None if parsing fails
    """
    date_formats = [
        "%Y-%m-%d",           # 2025-09-15
        "%d/%m/%Y",           # 15/09/2025
        "%m/%d/%Y",           # 09/15/2025
        "%d-%m-%Y",           # 15-09-2025
        "%B %d, %Y",          # September 15, 2025
        "%d %B %Y",           # 15 September 2025
        "%Y-%m-%d %H:%M:%S",  # 2025-09-15 10:00:00
    ]
    
    date_str = str(date_str).strip()
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Try to extract just the date part if it contains time
    if " " in date_str:
        date_part = date_str.split(" ")[0]
        return parse_event_date(date_part)
    
    return None


def create_event_hash(event: Dict[str, Any]) -> str:
    """
    Create a unique hash for an event based on name and date.
    
    Args:
        event (Dict[str, Any]): Event dictionary
        
    Returns:
        str: Hash string for deduplication
    """
    import hashlib
    
    # Create hash from event name and date
    hash_string = f"{event['event_name'].lower().strip()}_{event['event_date']}"
    return hashlib.md5(hash_string.encode()).hexdigest()


if __name__ == "__main__":
    # Test the module
    test_response = '''
    [
      {
        "event_name": "London Tech Hackathon",
        "event_date": "2025-09-15",
        "event_type": "hackathon",
        "event_url": "https://example.com/hackathon",
        "description": "A 48-hour hackathon focused on building innovative tech solutions with mentorship from industry experts.",
        "ticket_price": "Free",
        "venue": "Google Campus London, Shoreditch",
        "speakers": "Dr. Jane Smith (DeepMind), John Doe (TechStars)"
      }
    ]
    '''

    events = parse_openai_response(test_response)
    print(f"Parsed {len(events)} events:")
    for event in events:
        print(f"- {event['event_name']} on {event['event_date']}")
        print(f"  Price: {event['ticket_price']}")
        print(f"  Venue: {event['venue']}")
        print(f"  Hash: {create_event_hash(event)}")
