# Docker Setup and Testing Guide

## 🐳 What We Built

A Docker container that packages your event finder application so it can run anywhere - locally or on AWS ECS.

## 📁 Files Created

- **Dockerfile** - Blueprint for building the container image
- **.dockerignore** - Files to exclude from the image (secrets, cache, docs)
- **docker-compose.yml** - Easy way to run container locally with volumes and env vars

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended for Local Testing)

```bash
# Build and run in one command
docker-compose up

# Run in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove container
docker-compose down
```

### Option 2: Using Docker Commands Directly

```bash
# 1. Build the image
docker build -t event-finder .

# 2. Run the container
docker run --env-file .env -v $(pwd)/data:/app/data event-finder

# 3. Run with specific environment variables
docker run \
  -e OPENAI_API_KEY="sk-proj-..." \
  -e AWS_REGION="eu-west-1" \
  -e SES_FROM_EMAIL="londoneventsaisummary@gmail.com" \
  -e SES_TO_EMAIL="butler.will1@gmail.com" \
  -v $(pwd)/data:/app/data \
  event-finder
```

## 📦 What Happens During Build

```bash
docker build -t event-finder .
```

1. ✅ Downloads Python 3.11 base image
2. ✅ Installs dependencies (boto3, openai, pandas, etc.)
3. ✅ Copies your Python code into the image
4. ✅ Creates `/app/data` directory for CSV storage
5. ✅ Sets up the command to run `python main.py`

**What's NOT included:**
- ❌ `.env` file (secrets stay out!)
- ❌ `events_log.csv` (will be volume mounted)
- ❌ Documentation files
- ❌ Python cache files

## 🔍 Understanding the Setup

### Volume Mount: `-v $(pwd)/data:/app/data`

**What it does:**
- Maps your local `data/` directory to `/app/data` inside container
- CSV file persists between container runs
- You can inspect the CSV on your computer

**Visual:**
```
Your Computer                    Container
─────────────                    ─────────
/Users/wbutler/Documents/Github/llm-rag-event-discovery-pipeline/
  └── data/
      └── events_log.csv  ←──→  /app/data/events_log.csv
```

### Environment Variables: `--env-file .env`

**What it does:**
- Reads your `.env` file
- Injects variables into the container at runtime
- Secrets never stored in the image

**Alternative:** Pass variables individually with `-e`

## 🧪 Testing Checklist

### Before First Run

- [ ] `.env` file exists with all required variables
- [ ] `data/` directory exists (or will be created automatically)
- [ ] AWS credentials configured (`aws configure`)
- [ ] SES emails verified in AWS console
- [ ] Docker is running

### First Test Run

```bash
# Build the image
docker build -t event-finder .

# Expected output:
# [+] Building 45.2s (15/15) FINISHED
# => => naming to docker.io/library/event-finder

# Run the container
docker-compose up

# Expected output:
# Starting event search...
# Loading queries from data/queries.txt
# Found X events...
# 📧 Sending email digest...
# ✅ Email sent successfully!
```

### Verify Success

1. **Check console output** - Should see events found and email sent
2. **Check data/events_log.csv** - Should have new events
3. **Check your email** - Should receive digest at butler.will1@gmail.com
4. **Run again** - Should not duplicate events (deduplication working)

## 🔧 Common Commands

### Build and Run

```bash
# Build image
docker build -t event-finder .

# Run once and remove container after
docker run --rm --env-file .env -v $(pwd)/data:/app/data event-finder

# Run with docker-compose
docker-compose up
```

### Debugging

```bash
# Run container interactively (get a shell)
docker run -it --env-file .env -v $(pwd)/data:/app/data event-finder /bin/bash

# Inside container, you can:
ls -la                    # See files
cat src/llm_rag_event_discovery_pipeline/config.py             # View code
python main.py            # Run manually
env | grep SES            # Check environment variables

# View logs from last run
docker-compose logs

# Check if image was built correctly
docker images | grep event-finder
```

### Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove image
docker rmi event-finder

# Remove all unused images and containers
docker system prune -a
```

## 📊 Image Size

```bash
# Check image size
docker images event-finder

# Expected: ~500-600 MB
# - Python base: ~400 MB
# - Dependencies: ~100-200 MB
```

## 🔐 Security Notes

### ✅ What's Safe

- Image can be shared publicly (no secrets inside)
- Can be pushed to ECR without exposing credentials
- Environment variables injected at runtime only

### ⚠️ What to Protect

- `.env` file (never commit to git, never copy to image)
- AWS credentials (use IAM roles on ECS)
- `data/events_log.csv` (contains event data, use S3 in production)

## 🚀 Next Steps

### Current State: Local Docker with Volume

✅ Container runs locally
✅ CSV stored in local `data/` directory
✅ Environment variables from `.env` file
✅ AWS credentials from `~/.aws/credentials`

### Next Phase: S3 Integration

1. Create S3 bucket for CSV storage
2. Modify `memory.py` to read/write from S3
3. Test locally with S3
4. Remove volume mount (no longer needed)

### Final Phase: AWS ECS Deployment

1. Create ECR repository
2. Push image to ECR
3. Create ECS task definition
4. Set up IAM role with S3 and SES permissions
5. Create EventBridge schedule (Sunday 9am)
6. Test manual ECS task run
7. Enable schedule

## 🐛 Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Fix:** Make sure Docker Desktop is running

### Error: "SES_FROM_EMAIL environment variable is required"

**Fix:** Make sure `.env` file exists and has `SES_FROM_EMAIL=...`

### Error: "No such file or directory: events_log.csv"

**Fix:** Make sure volume is mounted: `-v $(pwd)/data:/app/data`

### Error: "Permission denied" when writing CSV

**Fix:** Make sure `data/` directory exists and is writable:
```bash
mkdir -p data
chmod 755 data
```

### Container exits immediately

**Fix:** Check logs:
```bash
docker-compose logs
```

### Events are duplicated on each run

**Fix:** Volume mount not working. Check:
```bash
ls -la data/events_log.csv  # Should exist and grow over time
```

## 💡 Tips

- **Rebuild after code changes:** `docker build -t event-finder .`
- **Use docker-compose for convenience:** Easier than long docker run commands
- **Check logs:** `docker-compose logs -f` to see real-time output
- **Test locally first:** Validate everything works before pushing to AWS
- **Keep .env updated:** If you change email addresses or keys

## 📚 Resources

- Docker documentation: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Best practices: https://docs.docker.com/develop/dev-best-practices/

---

Ready to test? Run:

```bash
docker-compose up
```

And check your email! 📧
