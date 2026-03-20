# 🚀 AWS Deployment Guide

This guide explains how to deploy your London Events AI Agent to AWS for automated, scheduled execution.

---

## 🎯 Deployment Overview

Your application needs to run **on a schedule** (e.g., daily) to:
1. Search for new London events using GPT-5
2. Store them in a vector database (Weaviate)
3. Send you an email digest via AWS SES

---

## 🏗️ AWS Architecture Options

### **Option 1: ECS Fargate + Scheduled Tasks (RECOMMENDED)** ⭐

**What it is:**
- **ECS (Elastic Container Service)**: AWS's container orchestration service
- **Fargate**: Serverless compute for containers (no servers to manage)
- **EventBridge Scheduler**: Triggers your container on a schedule (e.g., daily at 9 AM)

**How it works:**
```
EventBridge (9 AM daily)
    ↓
ECS Fargate Task starts
    ↓
Your Docker container runs
    ↓
Connects to Weaviate (separate container)
    ↓
Sends email via SES
    ↓
Task stops (you only pay for runtime)
```

**Components:**

| Technology | Purpose | Cost |
|------------|---------|------|
| **ECR (Elastic Container Registry)** | Stores your Docker image | ~$0.10/GB/month |
| **ECS Fargate** | Runs your container on schedule | ~$0.04/vCPU/hour + $0.004/GB/hour |
| **EventBridge Scheduler** | Triggers daily execution | Free (under 1M invocations) |
| **ECS Task for Weaviate** | Runs Weaviate vector database 24/7 | ~$30-50/month |
| **EFS (Elastic File System)** | Persistent storage for Weaviate data | ~$0.30/GB/month |
| **AWS SES** | Sends email digests | $0.10 per 1,000 emails |
| **VPC** | Private network for containers | Free (NAT Gateway ~$32/month if needed) |

**Estimated Monthly Cost:** $35-60/month

**Pros:**
- ✅ Fully managed (no servers)
- ✅ Only pay for event-finder when it runs
- ✅ Weaviate data persists between runs
- ✅ Easy to scale
- ✅ Production-ready

**Cons:**
- ⚠️ Weaviate runs 24/7 (costs ~$30-40/month)
- ⚠️ More complex setup than Lambda

---

### **Option 2: Lambda + Managed Weaviate Cloud**

**What it is:**
- **Lambda**: Serverless functions (15-minute max runtime)
- **Weaviate Cloud**: Fully managed Weaviate (external service)
- **EventBridge**: Triggers Lambda on schedule

**How it works:**
```
EventBridge (9 AM daily)
    ↓
Lambda function runs (max 15 min)
    ↓
Connects to Weaviate Cloud (external)
    ↓
Sends email via SES
    ↓
Lambda stops
```

**Components:**

| Technology | Purpose | Cost |
|------------|---------|------|
| **Lambda** | Runs your Python code | First 1M requests free, then $0.20/1M |
| **EventBridge** | Triggers daily | Free |
| **Weaviate Cloud** | Managed vector database | $25-100/month (external) |
| **AWS SES** | Sends emails | $0.10 per 1,000 emails |

**Estimated Monthly Cost:** $25-100/month (mostly Weaviate Cloud)

**Pros:**
- ✅ Simplest AWS setup
- ✅ No container management
- ✅ Pay only when running
- ✅ Weaviate fully managed

**Cons:**
- ⚠️ 15-minute Lambda timeout (may be tight for GPT-5 agentic search)
- ⚠️ Weaviate Cloud is external (additional service)
- ⚠️ Less control over Weaviate

---

### **Option 3: EC2 + Cron Job (Traditional)**

**What it is:**
- **EC2**: Virtual server running 24/7
- **Cron**: Linux scheduler
- **Docker Compose**: Runs both containers on same server

**How it works:**
```
EC2 instance (always running)
    ↓
Cron triggers at 9 AM
    ↓
Docker Compose runs your containers
    ↓
Sends email via SES
```

**Components:**

| Technology | Purpose | Cost |
|------------|---------|------|
| **EC2 (t3.small)** | Virtual server | ~$15/month (24/7) |
| **EBS Volume** | Disk storage | ~$8/month (80 GB) |
| **AWS SES** | Sends emails | $0.10 per 1,000 emails |

**Estimated Monthly Cost:** $23-25/month

**Pros:**
- ✅ Cheapest option
- ✅ Full control
- ✅ Simple architecture (like your local setup)
- ✅ Can SSH in to debug

**Cons:**
- ⚠️ Server runs 24/7 (even when not searching)
- ⚠️ You manage OS updates, security patches
- ⚠️ Single point of failure
- ⚠️ Not "serverless"

---

## 📊 Technology Breakdown

### **Core AWS Services**

#### **1. ECR (Elastic Container Registry)**
- **What**: Docker image storage (like Docker Hub, but private)
- **Why**: Stores your `event-finder` Docker image
- **How**: Push your image once, ECS pulls it when running tasks

#### **2. ECS (Elastic Container Service)**
- **What**: Container orchestration (manages Docker containers)
- **Why**: Runs your containers in the cloud
- **Components**:
  - **Cluster**: Logical grouping of tasks
  - **Task Definition**: Blueprint (which image, CPU, memory, env vars)
  - **Service**: Keeps Weaviate running 24/7
  - **Scheduled Task**: Runs event-finder daily

#### **3. Fargate**
- **What**: Serverless compute engine for containers
- **Why**: No servers to manage (AWS handles infrastructure)
- **How**: You specify CPU/memory, AWS provisions it

#### **4. EventBridge (formerly CloudWatch Events)**
- **What**: Serverless event bus and scheduler
- **Why**: Triggers your event-finder daily (like cron)
- **Example**: `cron(0 9 * * ? *)` = 9 AM UTC daily

#### **5. EFS (Elastic File System)**
- **What**: Network file system (like a shared drive)
- **Why**: Weaviate needs persistent storage for vector data
- **How**: Mounts to Weaviate container at `/var/lib/weaviate`

#### **6. AWS SES (Simple Email Service)**
- **What**: Email sending service
- **Why**: Sends your daily event digest
- **Setup Required**:
  - Verify sender email (`londoneventsaisummary@gmail.com`)
  - Verify recipient email (`butler.will1@gmail.com`)
  - Request production access (starts in sandbox mode)

#### **7. VPC (Virtual Private Cloud)**
- **What**: Private network in AWS
- **Why**: Containers communicate securely
- **Components**:
  - **Subnets**: Network segments (public/private)
  - **Security Groups**: Firewall rules
  - **NAT Gateway**: Allows private containers to access internet (for OpenAI API)

#### **8. Secrets Manager (Optional but Recommended)**
- **What**: Secure storage for API keys
- **Why**: Don't hardcode `OPENAI_API_KEY` in environment variables
- **How**: Store secrets, ECS retrieves them at runtime
- **Cost**: $0.40/secret/month + $0.05 per 10,000 API calls

---

## 🔄 Deployment Flow (ECS Fargate - Recommended)

### **Step 1: Prepare Your Application**
1. ✅ **Already done**: Your app is Dockerized
2. ✅ **Already done**: Environment variables in `.env`
3. ⚠️ **Need to do**: Update `WEAVIATE_URL` for AWS
4. ⚠️ **Need to do**: Ensure AWS credentials work (SES)

### **Step 2: Push Docker Image to ECR**
```bash
# Build your image
docker build -t event-finder .

# Tag for ECR
docker tag event-finder:latest <account-id>.dkr.ecr.eu-west-1.amazonaws.com/event-finder:latest

# Push to ECR
docker push <account-id>.dkr.ecr.eu-west-1.amazonaws.com/event-finder:latest
```

### **Step 3: Set Up Infrastructure**

**A. Create VPC** (or use default)
- Public subnet (for NAT Gateway)
- Private subnet (for containers)
- Security groups (allow Weaviate port 8080 internally)

**B. Create EFS for Weaviate**
- File system for persistent data
- Mount targets in private subnets

**C. Create ECS Cluster**
- Name: `london-events-cluster`
- Type: Fargate

**D. Create Task Definitions**

**Weaviate Task Definition:**
```json
{
  "family": "weaviate-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "weaviate",
      "image": "semitechnologies/weaviate:1.23.7",
      "portMappings": [{"containerPort": 8080}],
      "environment": [
        {"name": "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED", "value": "true"},
        {"name": "PERSISTENCE_DATA_PATH", "value": "/var/lib/weaviate"},
        {"name": "ENABLE_MODULES", "value": "text2vec-openai"}
      ],
      "secrets": [
        {"name": "OPENAI_APIKEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "mountPoints": [
        {
          "sourceVolume": "weaviate-data",
          "containerPath": "/var/lib/weaviate"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "weaviate-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx"
      }
    }
  ]
}
```

**Event Finder Task Definition:**
```json
{
  "family": "event-finder-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "event-finder",
      "image": "<account-id>.dkr.ecr.eu-west-1.amazonaws.com/event-finder:latest",
      "environment": [
        {"name": "WEAVIATE_URL", "value": "http://weaviate.local:8080"},
        {"name": "MODEL_NAME", "value": "gpt-5"},
        {"name": "REASONING_EFFORT", "value": "medium"},
        {"name": "AWS_REGION", "value": "eu-west-1"},
        {"name": "SES_FROM_EMAIL", "value": "londoneventsaisummary@gmail.com"},
        {"name": "SES_TO_EMAIL", "value": "butler.will1@gmail.com"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/event-finder",
          "awslogs-region": "eu-west-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**E. Create ECS Service (for Weaviate)**
- Task Definition: `weaviate-task`
- Desired Count: 1 (always running)
- Launch Type: Fargate
- VPC: Private subnet
- Service Discovery: Enable (so event-finder can find it)

**F. Create EventBridge Rule**
- Schedule: `cron(0 9 * * ? *)` (9 AM UTC daily)
- Target: ECS Task
- Task Definition: `event-finder-task`
- Launch Type: Fargate
- VPC: Same as Weaviate
- Security Group: Allow outbound to internet (OpenAI) and Weaviate

---

## 🔐 Security Considerations

### **1. API Keys**
- ✅ Use **Secrets Manager** for `OPENAI_API_KEY`
- ✅ Use **IAM roles** for AWS permissions (no hardcoded credentials)
- ❌ Don't put API keys in Docker image or environment variables

### **2. Network Security**
- ✅ Run containers in **private subnets**
- ✅ Use **NAT Gateway** for outbound internet (OpenAI API)
- ✅ **Security Groups**: Only allow Weaviate port 8080 between containers
- ❌ Don't expose Weaviate to public internet

### **3. Email Security**
- ✅ Verify both sender and recipient in SES
- ✅ Request production access (sandbox limits to verified emails)
- ✅ Use **DKIM** and **SPF** records for better deliverability

---

## 💰 Cost Breakdown (ECS Fargate Option)

### **Monthly Costs:**

| Service | Usage | Cost |
|---------|-------|------|
| **Weaviate (24/7)** | 0.5 vCPU, 1 GB RAM | ~$18/month |
| **Event Finder (daily)** | 0.25 vCPU, 0.5 GB, 10 min/day | ~$0.50/month |
| **EFS Storage** | 5 GB | ~$1.50/month |
| **NAT Gateway** | Data transfer | ~$32/month |
| **ECR Storage** | 1 GB | ~$0.10/month |
| **Secrets Manager** | 2 secrets | ~$0.80/month |
| **SES** | 30 emails/month | ~$0.01/month |
| **CloudWatch Logs** | 1 GB | ~$0.50/month |

**Total: ~$53/month**

### **Cost Optimization Tips:**

1. **Skip NAT Gateway** (~$32/month savings)
   - Use **VPC Endpoints** for AWS services (SES, Secrets Manager)
   - Use **public subnet** with public IP for containers
   - ⚠️ Less secure (containers have public IPs)

2. **Use Smaller Weaviate Instance**
   - 0.25 vCPU, 0.5 GB RAM (~$9/month)
   - ⚠️ May be slower for large datasets

3. **Use EC2 Instead** (~$23/month total)
   - Single t3.small instance
   - Run Docker Compose
   - ⚠️ Less "cloud-native"

---

## 🎯 Recommended Approach

### **For You (Personal Project):**

**Option: EC2 + Docker Compose** 💰

**Why:**
- ✅ **Cheapest**: ~$23/month vs ~$53/month
- ✅ **Simplest**: Same as your local setup
- ✅ **Familiar**: You already have `docker-compose.yml`
- ✅ **Easy debugging**: SSH in and check logs
- ✅ **No VPC complexity**: Single server

**Setup:**
1. Launch EC2 t3.small instance (Ubuntu)
2. Install Docker and Docker Compose
3. Copy your code and `.env` file
4. Run `docker-compose up -d`
5. Set up cron job: `0 9 * * * cd /home/ubuntu/ai_agent && docker-compose run event-finder`

**When to upgrade to ECS Fargate:**
- You need high availability (auto-restart on failure)
- You want to scale (multiple searches per day)
- You want "serverless" (no server management)

---

## 📋 Next Steps (When Ready to Deploy)

1. **Choose deployment option** (EC2 recommended for cost)
2. **Set up AWS SES** (verify emails)
3. **Create EC2 instance** or **ECS infrastructure**
4. **Deploy application**
5. **Test email delivery**
6. **Set up monitoring** (CloudWatch alarms)

---

## 🆘 Support Resources

- **AWS Free Tier**: First 12 months (750 hours EC2 t2.micro free)
- **AWS Documentation**: https://docs.aws.amazon.com/
- **ECS Tutorial**: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/
- **SES Setup Guide**: Already in `guides/AWS_SES_SETUP.md`

---

**Ready to deploy?** Let me know which option you prefer, and I'll create the deployment scripts! 🚀


