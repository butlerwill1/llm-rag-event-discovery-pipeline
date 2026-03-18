# 🔄 Complete Process Flow - File by File

This document explains how each file works and how they interact with each other.

---

## 📋 File Overview

| File | Purpose | Called By | Calls |
|------|---------|-----------|-------|
| **main.py** | Orchestrates entire process | User/Docker | All other files |
| **config.py** | Loads environment variables | main.py, others | os.getenv() |
| **query_loader.py** | Manages search queries | main.py | queries.txt |
| **openai_client.py** | Calls OpenAI API for search | main.py | OpenAI API |
| **event_parser.py** | Parses OpenAI responses | main.py | None |
| **weaviate_client.py** | Vector DB operations | main.py | Weaviate, OpenAI |
| **email_service.py** | Sends email digests | main.py | AWS SES |
| **rag_query.py** | Interactive RAG queries | User (CLI) | weaviate_client.py |

---

## 🚀 Step-by-Step Process Flow

### **Step 1: Initialization** (main.py)

```python
# File: main.py
def main():
    # 1.1: Load environment variables
    from config import QUERIES_FILE  # Reads .env file
    
    # 1.2: Connect to Weaviate
    weaviate_store = WeaviateEventStore()  # weaviate_client.py
    
    # 1.3: Load search queries
    queries = load_queries()  # query_loader.py → queries.txt
```

**Files involved:**
- `config.py` - Loads `OPENAI_API_KEY`, `WEAVIATE_URL`, etc.
- `weaviate_client.py` - Connects to Weaviate on port 8080
- `query_loader.py` - Reads `queries.txt`

---

### **Step 2: Cleanup Old Events** (main.py → weaviate_client.py)

```python
# File: main.py
deleted_count = weaviate_store.cleanup_past_events()
```

**What happens:**
1. `weaviate_client.py` gets today's date
2. Queries Weaviate for events where `eventDate < today`
3. Deletes each old event by UUID
4. Returns count of deleted events

**Files involved:**
- `weaviate_client.py` - `cleanup_past_events()` method

---

### **Step 3: Search for Events** (main.py → openai_client.py)

```python
# File: main.py
for query in queries:
    client = EventSearchClient()  # openai_client.py
    response = client.search_events(query)
```

**What happens in openai_client.py:**
```python
# File: openai_client.py
def search_events(self, query: str):
    # 3.1: Build prompt
    prompt = f"Find London tech events for: {query}"
    
    # 3.2: Call OpenAI API
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # 3.3: Return raw JSON response
    return response.choices[0].message.content
```

**Files involved:**
- `openai_client.py` - Calls OpenAI API with web search
- `config.py` - Provides `MODEL_NAME`, `OPENAI_API_KEY`

---

### **Step 4: Parse Events** (main.py → event_parser.py)

```python
# File: main.py
events = parse_openai_response(response)  # event_parser.py
```

**What happens in event_parser.py:**
```python
# File: event_parser.py
def parse_openai_response(response: str):
    # 4.1: Parse JSON
    data = json.loads(response)
    
    # 4.2: Extract events array
    events = data.get("events", [])
    
    # 4.3: Validate and normalize each event
    for event in events:
        # Ensure required fields exist
        event.setdefault("event_name", "Unknown")
        event.setdefault("event_date", "TBA")
        # ... etc
    
    return events
```

**Files involved:**
- `event_parser.py` - Parses and validates event data

---

### **Step 5: Deduplicate Events** (main.py → weaviate_client.py)

```python
# File: main.py
for event in all_new_events:
    if not weaviate_store.is_duplicate(event):
        # Add event
```

**What happens in weaviate_client.py:**
```python
# File: weaviate_client.py
def is_duplicate(self, event):
    # 5.1: Fast path - Check exact URL match
    if url_exists_in_db(event['event_url']):
        return True  # Duplicate!
    
    # 5.2: RAG-powered check
    return self._is_duplicate_with_llm(event)

def _is_duplicate_with_llm(self, event):
    # 5.3: Retrieve similar events (vector search)
    similar_events = weaviate.query.get("Event").with_near_text({
        "concepts": [f"{event['event_name']} {event['description']}"],
        "certainty": 0.85
    }).with_limit(5).do()
    
    # 5.4: Ask LLM to decide
    prompt = f"""
    New Event: {event}
    Similar Events: {similar_events}
    Is this a duplicate? Answer JSON: {{"is_duplicate": bool, "reason": str}}
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result["is_duplicate"]
```

**Files involved:**
- `weaviate_client.py` - Deduplication logic
- `openai_client.py` (indirectly) - LLM decision via OpenAI API

---

### **Step 6: Add New Events** (main.py → weaviate_client.py)

```python
# File: main.py
event['date_logged'] = datetime.now().isoformat()
weaviate_store.add_event(event)
newly_added_events.append(event)
```

**What happens in weaviate_client.py:**
```python
# File: weaviate_client.py
def add_event(self, event):
    # 6.1: Prepare data object
    data_object = {
        "eventName": event['event_name'],
        "eventDate": event['event_date'],
        "eventType": event['event_type'],
        "eventUrl": event['event_url'],
        "description": event['description'],
        # ... all fields
    }
    
    # 6.2: Add to Weaviate (auto-generates embedding)
    self.client.data_object.create(
        data_object=data_object,
        class_name="Event"
    )
    # Weaviate automatically:
    # - Generates embedding via OpenAI text-embedding-3-small
    # - Stores in vector database
    # - Indexes for semantic search
```

**Files involved:**
- `weaviate_client.py` - Adds event to vector DB
- Weaviate service - Generates embeddings via OpenAI

---

### **Step 7: Generate Summary** (main.py → weaviate_client.py)

```python
# File: main.py
total_events = weaviate_store.get_event_count()
all_events = weaviate_store.get_all_events(limit=100)

# Count event types
event_types = {}
for event in all_events:
    event_type = event.get('event_type', 'unknown')
    event_types[event_type] = event_types.get(event_type, 0) + 1
```

**What happens in weaviate_client.py:**
```python
# File: weaviate_client.py
def get_event_count(self):
    result = self.client.query.aggregate("Event").with_meta_count().do()
    return result["data"]["Aggregate"]["Event"][0]["meta"]["count"]

def get_all_events(self, limit=100):
    results = self.client.query.get("Event", [
        "eventName", "eventDate", "eventType", ...
    ]).with_limit(limit).do()
    
    return results["data"]["Get"]["Event"]
```

**Files involved:**
- `weaviate_client.py` - Queries Weaviate for statistics

---

### **Step 8: Send Email** (main.py → email_service.py)

```python
# File: main.py
email_service = create_email_service_from_env()
email_sent = email_service.send_weekly_digest(newly_added_events, total_events)
```

**What happens in email_service.py:**
```python
# File: email_service.py
def send_weekly_digest(self, events, total_count):
    # 8.1: Build HTML email
    html_body = f"""
    <h1>🎯 {len(events)} New London Tech Events</h1>
    <ul>
    """
    
    for event in events:
        html_body += f"""
        <li>
            <strong>{event['event_name']}</strong><br>
            📅 {event['event_date']}<br>
            📍 {event.get('venue', 'TBA')}<br>
            <a href="{event['event_url']}">Details</a>
        </li>
        """
    
    html_body += "</ul>"
    
    # 8.2: Send via AWS SES
    ses_client = boto3.client('ses', region_name='eu-west-1')
    ses_client.send_email(
        Source=self.from_email,
        Destination={'ToAddresses': [self.to_email]},
        Message={
            'Subject': {'Data': f'🎯 {len(events)} New Events'},
            'Body': {'Html': {'Data': html_body}}
        }
    )
```

**Files involved:**
- `email_service.py` - Formats and sends email
- `config.py` - Provides `SES_FROM_EMAIL`, `SES_TO_EMAIL`, `AWS_REGION`
- AWS SES - Sends email

---

## 🔍 Alternative Flow: RAG Query (rag_query.py)

This is a separate tool for querying stored events:

```bash
python rag_query.py "What AI events are happening?"
```

**What happens:**
```python
# File: rag_query.py
def main():
    # 1: Connect to Weaviate
    store = WeaviateEventStore()
    
    # 2: Search for relevant events
    events = store.search_events(query, limit=5)
    
    # 3: Build context
    context = format_events_for_llm(events)
    
    # 4: Ask LLM to answer question
    prompt = f"""
    Events in database:
    {context}
    
    Question: {query}
    Answer based on the events above.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    print(response.choices[0].message.content)
```

**Files involved:**
- `rag_query.py` - RAG query tool
- `weaviate_client.py` - Searches events
- OpenAI API - Generates answer

---

## 📊 Data Flow Summary

```
User Input (queries.txt)
    ↓
OpenAI API (web search)
    ↓
Raw JSON Response
    ↓
event_parser.py (parse & validate)
    ↓
Structured Events
    ↓
weaviate_client.py (deduplicate via RAG)
    ↓
New Events Only
    ↓
Weaviate Vector DB (store with embeddings)
    ↓
email_service.py (format & send)
    ↓
AWS SES (deliver email)
    ↓
User's Inbox ✉️
```

---

## 🎯 Key Interactions

### **main.py ↔ weaviate_client.py**
- Most important relationship
- main.py calls weaviate_client for all storage operations
- weaviate_client handles deduplication, storage, retrieval

### **weaviate_client.py ↔ OpenAI API**
- Generates embeddings for vector search
- LLM decisions for deduplication
- Two different models: `text-embedding-3-small` and `gpt-4o`

### **main.py ↔ openai_client.py**
- One-way: main.py calls openai_client
- openai_client searches web for events
- Returns raw JSON

### **main.py ↔ event_parser.py**
- One-way: main.py calls event_parser
- Converts raw JSON to structured Python dicts
- Validates and normalizes data

### **main.py ↔ email_service.py**
- One-way: main.py calls email_service
- Passes newly added events
- email_service formats and sends

---

## 🔧 Configuration Files

### **config.py**
```python
# Loads from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")
SES_TO_EMAIL = os.getenv("SES_TO_EMAIL")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
QUERIES_FILE = "queries.txt"
```

### **queries.txt**
```
London AI events this week
London hackathons in March
Tech meetups in Shoreditch
```

---

## 🐳 Docker Flow

When running in Docker:

```
docker-compose up
    ↓
Starts two services:
    1. weaviate (vector database)
    2. event-finder (Python app)
    ↓
event-finder waits for weaviate to be healthy
    ↓
Runs: python main.py
    ↓
(Same flow as above)
```

**Files involved:**
- `docker-compose.yml` - Orchestrates services
- `Dockerfile` - Builds Python app image
- `requirements.txt` - Python dependencies

---

This is the complete process flow! Each file has a specific responsibility and they work together to find, deduplicate, store, and email London tech events.

