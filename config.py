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
# Using GPT-5 with agentic search for intelligent, reasoning-based event discovery
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5")  # Reasoning model for agentic search
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium")  # minimal, low, medium, high, or xhigh
USER_LOCATION = "London, GB"

# AWS SES Configuration
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")  # Must be verified in SES
SES_TO_EMAIL = os.getenv("SES_TO_EMAIL", "butler.will1@gmail.com")

# CSV Schema
CSV_COLUMNS = ["event_name", "event_date", "event_type", "event_url", "description", "ticket_price", "venue", "speakers", "date_logged"]

# Prompt template for OpenAI Agentic Search
PROMPT_TEMPLATE = """
You are an intelligent event discovery agent. Use web search to find upcoming events based on this query:
"{query}"

SEARCH STRATEGY:
- Perform multiple searches if needed to find comprehensive results
- Check official event platforms (Eventbrite, Meetup, Luma, etc.)
- Look for event aggregator sites specific to London
- Verify event details from official sources
- Cross-reference information to ensure accuracy

CRITICAL DATE REQUIREMENT: Today's date is {today_date}.
- ONLY include events with dates on or after {today_date}
- REJECT any events from the past
- Double-check each event date before including it
- If a date is unclear, search for more information to confirm

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
