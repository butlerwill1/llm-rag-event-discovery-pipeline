# 🧪 Local Testing Guide

This guide walks you through testing the LLM RAG Event Discovery Pipeline on your local machine.

---

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **Python 3.11+** installed (for non-Docker testing)
- ✅ **OpenAI API Key** (for event search and embeddings)
- ✅ **AWS SES configured** (for email sending) - Optional for initial testing

---

## 🚀 Quick Start (Recommended)

### Option 1: Full Docker Setup (Easiest)

This runs everything in Docker - both Weaviate and your Python app.

```bash
# 1. Make sure Docker Desktop is running
docker --version  # Should show Docker version

# 2. Start everything
docker-compose up

# That's it! The system will:
# - Start Weaviate vector database
# - Wait for Weaviate to be healthy
# - Build and run your Python app
# - Search for events, deduplicate, store, and email
```

**What you'll see:**
```
✅ Weaviate starting on port 8080...
✅ Weaviate is healthy
✅ Building event-finder image...
✅ Starting event-finder...
LLM RAG Event Discovery Pipeline
==================================================
Initializing Weaviate...
✅ Connected to Weaviate
🧹 Cleaning up past events...
🔍 Searching for events...
💾 Processing events...
📧 Sending email digest...
✅ Event search completed!
```

**To stop:**
```bash
# Press Ctrl+C, then:
docker-compose down
```

---

### Option 2: Hybrid Setup (Best for Development)

Run Weaviate in Docker, but run your Python app locally. This is faster for testing code changes.

```bash
# 1. Start only Weaviate
docker-compose up -d weaviate

# 2. Wait for Weaviate to be ready (check health)
docker-compose ps  # Should show weaviate as "healthy"

# 3. Install Python dependencies (if not already done)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. Run your app locally
python main.py
```

**Advantages:**
- ✅ Faster iteration (no Docker rebuild)
- ✅ Easier debugging
- ✅ Can use your IDE's debugger
- ✅ See print statements immediately

**To stop Weaviate:**
```bash
docker-compose down
```

---

## ⚙️ Configuration Check

### 1. Verify your `.env` file

Make sure your `.env` file has these variables:

```bash
# Required for event search
OPENAI_API_KEY=sk-proj-...

# Required for email (can skip for initial testing)
SES_FROM_EMAIL=londoneventsaisummary@gmail.com
SES_TO_EMAIL=butler.will1@gmail.com
AWS_REGION=eu-west-1

# Optional (has defaults)
MODEL_NAME=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
WEAVIATE_URL=http://localhost:8080  # For local Python, use localhost
```

### 2. Check your queries

Edit `data/queries.txt` to customize what events to search for:

```bash
cat data/queries.txt
```

Example queries:
```
London AI events this week
London hackathons in March
Tech meetups in Shoreditch
```

---

## 🧪 Step-by-Step Testing

### Test 1: Verify Weaviate is Running

```bash
# Start Weaviate
docker-compose up -d weaviate

# Check if it's healthy
curl http://localhost:8080/v1/.well-known/ready

# Should return: {"status": "ok"}
```

**Troubleshooting:**
- If port 8080 is already in use: `lsof -i :8080` to find what's using it
- If Weaviate won't start: `docker-compose logs weaviate`

---

### Test 2: Test OpenAI Connection

```bash
# Quick test script
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': 'Say hello'}]
)
print('✅ OpenAI connection works!')
print(response.choices[0].message.content)
"
```

**Expected output:**
```
✅ OpenAI connection works!
Hello! How can I assist you today?
```

---

### Test 3: Test Weaviate Connection

```bash
python -c "
import weaviate
import os

client = weaviate.Client('http://localhost:8080')
print('✅ Weaviate connection works!')
print(f'Schema: {client.schema.get()}')
"
```

---

### Test 4: Run the Full Pipeline (Without Email)

To test without sending emails, you can temporarily comment out the email section:

```bash
# Run the app
python main.py

# Or with Docker
docker-compose up event-finder
```

**What to watch for:**
1. ✅ Connects to Weaviate
2. ✅ Cleans up past events
3. ✅ Searches for events (calls OpenAI)
4. ✅ Parses events
5. ✅ Deduplicates using RAG
6. ✅ Stores new events in Weaviate
7. ✅ Shows summary
8. ⚠️ Email might fail if AWS SES not configured (that's OK for testing)

---

### Test 5: Query Stored Events

After running the pipeline, check what's stored:

```bash
# Use the RAG query tool
python rag_query.py "What AI events are happening?"

# Or check directly
python -c "
from weaviate_client import WeaviateEventStore

store = WeaviateEventStore()
count = store.get_event_count()
print(f'Total events in database: {count}')

events = store.get_all_events(limit=5)
for event in events:
    print(f\"  • {event['event_name']} - {event['event_date']}\")
"
```

---

### Test 6: Test Deduplication

Run the pipeline twice to test deduplication:

```bash
# First run
python main.py

# Note how many events were added, e.g., "Logged 15 new events"

# Second run (immediately after)
python main.py

# Should see: "Logged 0 new events (skipped 15 duplicates)"
```

---

## 🔍 Interactive Testing

Use interactive mode to test individual queries:

```bash
python main.py --interactive

# Commands:
> search     # Search for events with a custom query
> find       # Search stored events
> summary    # Show database statistics
> list       # Show all queries
> quit       # Exit
```

---

## 📊 Monitoring & Debugging

### View Weaviate Data

Access Weaviate's console in your browser:
```
http://localhost:8080/v1/schema
```

### View Docker Logs

```bash
# All logs
docker-compose logs -f

# Just Weaviate
docker-compose logs -f weaviate

# Just your app
docker-compose logs -f event-finder
```

### Check Docker Volumes

```bash
# List volumes
docker volume ls

# Inspect weaviate-data volume
docker volume inspect weaviate-data

# See disk usage
docker system df -v
```

---

## 🧹 Cleanup & Reset

### Reset Everything (Fresh Start)

```bash
# Stop containers and remove volumes (deletes all events!)
docker-compose down -v

# Remove built images
docker rmi event-finder:latest

# Start fresh
docker-compose up
```

### Keep Data, Just Restart

```bash
# Stop containers but keep volumes
docker-compose down

# Start again (data persists)
docker-compose up
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: "Port 8080 already in use"

```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process or change Weaviate port in docker-compose.yml
```

### Issue 2: "OpenAI API key not found"

```bash
# Check .env file exists
cat .env | grep OPENAI_API_KEY

# Make sure it's loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Issue 3: "Weaviate connection refused"

```bash
# Make sure Weaviate is running
docker-compose ps

# Check Weaviate logs
docker-compose logs weaviate

# Restart Weaviate
docker-compose restart weaviate
```

### Issue 4: "Email sending failed"

This is expected if AWS SES isn't configured. Options:
1. Skip email testing initially (focus on event finding)
2. Configure AWS SES (see `docs/guides/AWS_SES_SETUP.md`)
3. Comment out email section in `main.py` temporarily

### Issue 5: "No events found"

- Check your queries in `data/queries.txt` - make them more specific
- Check OpenAI API quota/billing
- Try a simpler query: "London tech events this week"

---

## 📈 Success Criteria

Your local testing is successful if:

- ✅ Weaviate starts and shows "healthy"
- ✅ Python app connects to Weaviate
- ✅ OpenAI API returns event data
- ✅ Events are parsed correctly
- ✅ Duplicates are detected on second run
- ✅ Events are stored in Weaviate
- ✅ You can query events with `rag_query.py`
- ✅ (Optional) Email is sent successfully

---

## 🎯 Next Steps After Local Testing

Once local testing works:

1. **Optimize queries** - Refine `data/queries.txt` for better results
2. **Test email** - Configure AWS SES and test email delivery
3. **Schedule runs** - Set up cron job or use Docker restart policies
4. **Deploy to AWS** - Use Terraform to deploy to ECS Fargate
5. **Monitor costs** - Track OpenAI API usage

---

## 💡 Pro Tips

1. **Use hybrid setup during development** - Faster iteration
2. **Keep Weaviate running** - No need to restart between tests
3. **Check logs frequently** - `docker-compose logs -f`
4. **Test with small query sets first** - Avoid burning API credits
5. **Use `rag_query.py`** - Great for exploring stored events

---

Happy testing! 🚀
