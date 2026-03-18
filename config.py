"""
Configuration settings for the Event Finding AI Agent
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")

# File paths
# Support both local development and Docker container
DATA_DIR = os.getenv("DATA_DIR", "data")  # Use 'data' directory for Docker, current dir for local
QUERIES_FILE = "queries.txt"
EVENTS_LOG_FILE = os.path.join(DATA_DIR, "events_log.csv")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# OpenAI Model Configuration
MODEL_NAME = "gpt-4o"  # Using gpt-4o for higher rate limits
USER_LOCATION = "London, GB"

# AWS SES Configuration
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")  # Must be verified in SES
SES_TO_EMAIL = os.getenv("SES_TO_EMAIL", "butler.will1@gmail.com")

# CSV Schema
CSV_COLUMNS = ["event_name", "event_date", "event_type", "event_url", "description", "ticket_price", "venue", "speakers", "date_logged"]

# Prompt template for OpenAI
PROMPT_TEMPLATE = """
Please use the web to search for upcoming events based on the following query:
"{query}"

IMPORTANT: Only return FUTURE events that have NOT happened yet. Today's date is {today_date}.
- Only include events with dates on or after {today_date}
- Do NOT include events from the past
- Do NOT include events that already happened
- Verify the event date is in the future before including it

Return a JSON object for each event that matches the following criteria:
- Must take place in London or nearby areas
- Must be a real, scheduled event happening in the future (on or after {today_date})
- Must fall into one of the categories the user is interested in
- Must have a confirmed date and registration/information available

Each JSON object should include:
- event_name: The full name of the event
- event_date: The event date in YYYY-MM-DD format
- event_type: The category/type of event (e.g., "hackathon", "networking", "conference", "marathon")
- event_url: The official website or registration page URL
- description: A paragraph-long summary of what the event is about, its purpose, and what attendees can expect
- ticket_price: The cost to attend (e.g., "Free", "£25", "£50-100", "Contact for pricing")
- venue: The location where the event takes place (venue name and area/address if available)
- speakers: Key speakers, presenters, or notable attendees if mentioned (or "TBA" if not announced)

Only return events in JSON format. Do not include summaries or explanations.
Return the events as a JSON array like this:
[
  {{
    "event_name": "Example Event",
    "event_date": "2025-09-15",
    "event_type": "hackathon",
    "event_url": "https://example.com/event",
    "description": "A 48-hour hackathon focused on building AI solutions for climate change. Teams will work on innovative projects with mentorship from industry experts.",
    "ticket_price": "Free",
    "venue": "Google Campus London, Shoreditch",
    "speakers": "Dr. Jane Smith (DeepMind), John Doe (Climate Tech Ventures)"
  }}
]
"""
