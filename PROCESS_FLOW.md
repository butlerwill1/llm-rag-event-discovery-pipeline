# Process Flow Documentation

Detailed execution flow and component interactions for the Event Discovery RAG Pipeline.

---

## File Overview

| File | Purpose | Dependencies |
|------|---------|--------------|
| **main.py** | Orchestration and execution flow | All components |
| **config.py** | Environment configuration | python-dotenv |
| **query_loader.py** | Query file management | queries.txt |
| **openai_client.py** | GPT-5 agentic web search | OpenAI SDK |
| **event_parser.py** | JSON response parsing | json, logging |
| **weaviate_client.py** | Vector database operations | Weaviate v4, sentence-transformers, OpenAI |
| **email_service.py** | Email digest generation | boto3 (AWS SES) |

---

## Execution Flow

### Step 1: Container Initialization

**ECS Task Startup:**
1. EventBridge triggers ECS task at scheduled time (Sunday 9 AM UTC)
2. ECS starts both containers:
   - Weaviate container (essential=false)
   - Event Finder container (essential=true)
3. Event Finder waits for Weaviate health check

**Component Initialization (main.py):**
```python
# Load configuration
from config import QUERIES_FILE, OPENAI_API_KEY, AWS_REGION

# Connect to Weaviate
weaviate_store = WeaviateEventStore()
# - Connects to localhost:8080 (Weaviate container)
# - Loads local embedding model (all-MiniLM-L6-v2)
# - Ensures Event collection schema exists

# Load search queries
queries = load_queries()  # Reads queries.txt
```

**Key Operations:**
- Environment variable loading via python-dotenv
- Weaviate connection with health check retry logic
- Local embedding model pre-loaded from Docker image layer
- Schema validation and creation if needed

---

### Step 2: Data Cleanup

**Remove Past Events:**
```python
deleted_count = weaviate_store.cleanup_past_events()
```

**Implementation (weaviate_client.py):**
1. Get current date
2. Query Weaviate: `eventDate < today`
3. Delete each past event by UUID
4. Return count of deleted events

**Purpose:**
- Reduce storage costs
- Keep database focused on future events
- Prevent stale data accumulation

---

### Step 3: Event Discovery

**Agentic Web Search (openai_client.py):**
```python
for query in queries:
    client = EventSearchClient()
    response = client.search_events(query)
```

**OpenAI Responses API Call:**
```python
response = self.client.responses.create(
    model="gpt-5",
    input=formatted_prompt,
    reasoning={"effort": "medium"},
    tools=[{
        "type": "web_search",
        "search_context_size": "high",
        "user_location": {
            "type": "approximate",
            "country": "GB",
            "city": "London"
        }
    }]
)
```

**What GPT-5 Does:**
1. Plans multi-step search strategy
2. Searches event platforms (Eventbrite, Meetup, Luma)
3. Cross-references information from multiple sources
4. Filters by date constraints (future events only)
5. Extracts structured data (name, date, venue, pricing)
6. Returns JSON array of events

**Key Features:**
- Reasoning-based search planning
- Geographic context (London)
- High search context for detailed information
- Structured JSON output

---

### Step 4: Response Parsing

**Parse JSON Response (event_parser.py):**
```python
# main.py
events = parse_openai_response(response)  # event_parser.py
```

**Parsing Logic (event_parser.py):**
```python
def parse_openai_response(response: str):
    # Parse JSON string
    data = json.loads(response)

    # Extract events array
    events = data if isinstance(data, list) else data.get("events", [])

    # Validate and normalize
    validated_events = []
    for event in events:
        if validate_event_structure(event):
            validated_events.append(event)

    return validated_events
```

**Validation:**
- Ensures required fields exist (name, date, URL)
- Normalizes date formats
- Filters out malformed events
- Logs parsing errors

---

### Step 5: RAG-Powered Deduplication

**Hybrid Deduplication Strategy:**

**Phase 1: Fast Path (Exact URL Match)**
```python
# weaviate_client.py
def is_duplicate(self, event):
    # Check for exact URL match
    results = events.query.fetch_objects(
        filters=Filter.by_property("eventUrl").equal(event["event_url"]),
        limit=1
    )
    if len(results.objects) > 0:
        return True  # Duplicate found
```

**Phase 2: Semantic Search (Local Embeddings)**
```python
# Generate embedding for new event
search_text = f"{event['event_name']} {event['description']}"
query_vector = self.embedding_model.encode(search_text).tolist()

# Vector similarity search
results = events.query.near_vector(
    near_vector=query_vector,
    certainty=0.85,  # 85% similarity threshold
    limit=5  # Get top 5 candidates
)
```

**Phase 3: LLM Analysis (GPT-4o)**
```python
# Build context from retrieved events
context = format_similar_events_for_llm(similar_events)

# Ask GPT-4o to make final decision
prompt = f"""
New Event: {event details}
Similar Events in Database: {context}

Rules:
1. Same name + same date = DUPLICATE
2. Same URL = DUPLICATE
3. Similar name but different date = NOT duplicate (recurring event)
4. Similar topic but different venue = NOT duplicate

Answer JSON: {{"is_duplicate": bool, "reason": str}}
"""

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.1  # Low temperature for consistency
)
```

**Why This Approach:**
- Fast path catches obvious duplicates (same URL)
- Vector search finds semantic similarities
- LLM provides nuanced decision-making (recurring events, similar topics)
- Higher accuracy than threshold-based similarity alone

---

### Step 6: Event Storage

**Add New Event (weaviate_client.py):**
```python
def add_event(self, event):
    # Prepare properties
    properties = {
        "eventName": event.get("event_name", ""),
        "eventDate": to_rfc3339(event.get("event_date", "")),
        "eventType": event.get("event_type", ""),
        "eventUrl": event.get("event_url", ""),
        "description": event.get("description", ""),
        "ticketPrice": event.get("ticket_price", ""),
        "venue": event.get("venue", ""),
        "speakers": event.get("speakers", ""),
        "dateLogged": to_rfc3339(datetime.now().isoformat())
    }

    # Generate embedding locally (no API cost!)
    text_to_embed = f"{event['event_name']} {event['description']} {event['event_type']} {event['venue']}"
    vector = self.embedding_model.encode(text_to_embed).tolist()

    # Store in Weaviate with vector
    events = self.client.collections.get("Event")
    uuid = events.data.insert(
        properties=properties,
        vector=vector
    )

    # Weaviate immediately writes to WAL on EFS
    return uuid
```

**Key Features:**
- Local embedding generation (all-MiniLM-L6-v2)
- No OpenAI embedding API costs
- Immediate WAL persistence to EFS
- 384-dimensional vectors

---

### Step 7: Email Digest Generation

**Format and Send Email (email_service.py):**
```python
# main.py
email_service = create_email_service_from_env()
email_sent = email_service.send_weekly_digest(
    newly_added_events,
    total_event_count
)
```

**Email Service Implementation:**
```python
# email_service.py
def send_weekly_digest(self, events, total_count):
    # Build HTML email body
    html_body = build_html_template(events, total_count)

    # Send via AWS SES
    ses_client = boto3.client('ses', region_name=self.aws_region)
    response = ses_client.send_email(
        Source=self.from_email,  # Must be verified in SES
        Destination={'ToAddresses': [self.to_email]},
        Message={
            'Subject': {
                'Data': f'New London Events - {len(events)} Found'
            },
            'Body': {
                'Html': {'Data': html_body}
            }
        }
    )

    return response['MessageId']
```

**Email Content:**
- Summary of new events found
- Event details (name, date, venue, pricing)
- Direct links to event pages
- Total events in database
- Professional HTML formatting

---

### Step 8: Container Shutdown

**Graceful Termination:**
```python
# main.py (finally block)
finally:
    # Clean up Weaviate connection
    if weaviate_store is not None:
        try:
            weaviate_store.client.close()
            logger.info("Weaviate connection closed")
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
```

**ECS Task Lifecycle:**
1. Event Finder container exits (code 0)
2. ECS detects essential container stopped
3. ECS sends SIGTERM to Weaviate container
4. Weaviate flushes WAL to EFS (30-second timeout)
5. ECS sends SIGKILL if needed
6. Task terminates
7. Data persisted on EFS for next run

**Data Safety:**
- WAL already flushed during event storage
- 30-second grace period for final cleanup
- EFS ensures durability
- No data loss on shutdown

---

## Key Technical Concepts

### Document-Level RAG (No Chunking)

This system uses **document-level RAG** rather than chunk-based RAG:

**Storage:**
- Each event = 1 vector (384 dimensions)
- No chunking needed (events are small, self-contained)
- Concatenate key fields: name + description + type + venue

**Retrieval:**
- Vector similarity search returns whole events
- Top 5 similar events passed to LLM
- LLM analyzes complete event context

**Why No Chunking:**
- Events are short (~100-300 words)
- Each event is semantically distinct
- Chunking would lose holistic meaning
- More efficient: 1 vector per event vs. multiple chunks

### Local vs. API Embeddings

**Local Embeddings (all-MiniLM-L6-v2):**
- Generated on-device (no API calls)
- 384 dimensions
- Fast inference (~10ms per event)
- Zero cost
- Pre-loaded in Docker image

**Cost Comparison:**
- OpenAI embeddings: $0.00002 per 1K tokens
- Local embeddings: $0.00 (free)
- For 100 events/week: ~$0.10/month saved

### Write-Ahead-Log (WAL) Persistence

**How It Works:**
1. Event added to Weaviate
2. Write to WAL on EFS (append-only)
3. Acknowledge to client
4. Update in-memory index
5. Periodic segment flush

**Recovery:**
- On startup, check WAL status
- Replay incomplete WAL entries
- Load completed segments
- Ready for queries

**Guarantees:**
- Every acknowledged write is durable
- Crash-safe (WAL on persistent storage)
- Fast writes (append-only)
- Automatic recovery

## Component Interactions

### main.py (Orchestrator)
**Calls:**
- `config.py` - Load environment variables
- `query_loader.py` - Load search queries
- `openai_client.py` - Perform web search
- `event_parser.py` - Parse JSON responses
- `weaviate_client.py` - Deduplication and storage
- `email_service.py` - Send digest

### weaviate_client.py (Vector Database)
**Calls:**
- Local embedding model (sentence-transformers)
- OpenAI GPT-4o (for deduplication decisions)
- Weaviate database (localhost:8080)

**Provides:**
- Event storage with vectors
- Duplicate detection (URL + RAG)
- Semantic search
- Event retrieval

### openai_client.py (Web Search)
**Calls:**
- OpenAI Responses API (GPT-5)
- Web search tool

**Provides:**
- Agentic event discovery
- Structured JSON output
- Multi-step search execution

### email_service.py (Notifications)
**Calls:**
- AWS SES (boto3)

**Provides:**
- HTML email formatting
- Digest delivery

---

## Configuration

### Environment Variables (.env)
```bash
# OpenAI
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-5
REASONING_EFFORT=medium

# AWS
AWS_REGION=eu-west-1
SES_FROM_EMAIL=verified@example.com
SES_TO_EMAIL=recipient@example.com

# Weaviate (Docker)
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051
```

### Search Queries (queries.txt)
```
London AI hackathons
# Lines starting with # are comments
# Add one query per line
```

---

## Deployment Architecture

### Local Development
```
docker-compose up
  ├── Weaviate container (port 8080)
  └── Event Finder container
      └── python main.py
```

### Production (AWS ECS)
```
EventBridge Scheduler (Sunday 9 AM UTC)
  ↓
ECS Fargate Task
  ├── Weaviate container (essential=false)
  │   └── EFS mount: /var/lib/weaviate
  └── Event Finder container (essential=true)
      ├── Pulls from ECR
      ├── Connects to Weaviate (localhost)
      ├── Calls OpenAI API
      ├── Sends email via SES
      └── Exits → Task terminates
```

### CI/CD Pipeline
```
git push origin main
  ↓
GitHub Actions
  ├── Build Docker image
  ├── Push to ECR
  └── ECS uses new image on next scheduled run
```

**Path-based filtering:**
- Changes to `terraform/` → No build
- Changes to `guides/` → No build
- Changes to `*.md` → No build
- Changes to `*.py` → Build and deploy

---

## Summary

This pipeline demonstrates a production-grade RAG system with:

**Technical Highlights:**
- Multi-model AI strategy (GPT-5 for search, GPT-4o for deduplication)
- Local embeddings for cost optimization
- Hybrid deduplication (URL + vector + LLM)
- Serverless architecture with ECS Fargate
- Infrastructure as Code with Terraform
- CI/CD with GitHub Actions
- Persistent storage with EFS and WAL
- Graceful container lifecycle management

**Data Engineering Practices:**
- Vector database for semantic search
- Document-level RAG (no chunking needed)
- Write-Ahead-Log for durability
- Automated data cleanup
- Structured logging and monitoring

**Cost Optimization:**
- Local embeddings (zero API cost)
- Scheduled execution (no idle compute)
- Path-based CI/CD filtering
- 7-day log retention
- Efficient Docker image caching

For architecture diagrams and visual representations, see [ARCHITECTURE.md](./ARCHITECTURE.md).

