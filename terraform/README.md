# Terraform Deployment for London Events AI Agent

This directory contains Terraform infrastructure-as-code for deploying the London Events AI Agent to AWS ECS Fargate.

## 🏗️ Architecture

The deployment creates a **cost-optimized, on-demand architecture**:

- **ECS Fargate Task** runs both Weaviate and Event Finder containers together
- **EFS** provides persistent storage for Weaviate's vector database
- **EventBridge Scheduler** triggers the task daily
- **No NAT Gateway** - uses public subnets to save ~$32/month

### Key Innovation: On-Demand Vector Database

Instead of running Weaviate 24/7 (~$30/month), we:
1. Run Weaviate and Event Finder in the **same ECS task**
2. Mount **EFS** for persistent storage
3. Task starts → Weaviate loads data from EFS → Event Finder runs → Task stops
4. **Saves ~90% on compute costs** (~$3/month vs ~$35/month)

## 📦 What Gets Created

| Resource | Purpose | Monthly Cost |
|----------|---------|--------------|
| VPC + Subnets | Network isolation | Free |
| ECS Cluster | Container orchestration | Free |
| ECS Task Definition | Multi-container blueprint | Free |
| EFS File System | Weaviate data persistence | ~$1.50 (5 GB) |
| ECR Repository | Docker image storage | ~$0.10 |
| Secrets Manager | OpenAI API key | ~$0.40 |
| CloudWatch Logs | Application logs | ~$0.50 |
| EventBridge Schedule | Daily trigger | Free |
| IAM Roles | Permissions | Free |

**Total: ~$3-5/month**

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with credentials
2. **Terraform** >= 1.0
3. **Docker** installed
4. **SES emails verified** (sender and recipient)

### Step 1: Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

Update these required values:
- `openai_api_key` - Your OpenAI API key
- `ses_from_email` - Verified sender email
- `ses_to_email` - Verified recipient email
- `owner` - The person or team responsible for the spend
- `cost_center` - The billing code, budget, or bucket you want to report against

### Step 2: Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### Step 3: Build and Push Docker Image

```bash
# Get ECR URL from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)
AWS_REGION=$(terraform output -raw aws_region)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URL

# Build and push (from project root)
cd ..
docker build -t event-finder .
docker tag event-finder:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

### Step 4: Verify Deployment

```bash
cd terraform

# Test manual run
aws ecs run-task \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --task-definition $(terraform output -raw task_definition_family) \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$(terraform output -json public_subnet_ids | jq -r '.[0]')],securityGroups=[$(terraform output -raw task_security_group_id)],assignPublicIp=ENABLED}"

# Watch logs
aws logs tail $(terraform output -raw cloudwatch_log_group) --follow
```

## 📁 Module Structure

```
terraform/
├── main.tf                    # Root configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example configuration
├── modules/
│   ├── vpc/                   # VPC, subnets, routing
│   ├── efs/                   # Persistent storage
│   ├── ecr/                   # Docker registry
│   ├── secrets/               # API key storage
│   ├── iam/                   # Roles and policies
│   ├── ecs/                   # Container orchestration
│   └── scheduler/             # Daily scheduling
```

## 🔧 Configuration Options

### Cost Optimization

```hcl
# Use NAT Gateway (more secure, +$32/month)
enable_nat_gateway = true

# Use public subnets (cheaper, less secure)
enable_nat_gateway = false  # Default
```

### Cost Allocation Tags

Terraform now applies these tags automatically to supported AWS resources:

- `Project`
- `Environment`
- `ManagedBy`
- `Owner`
- `CostCenter`

Use `tags` in `terraform.tfvars` for any extra reporting dimensions you want, such as
`Repository`, `Team`, or `Workload`.

To see these in AWS Cost Explorer or CUR, activate the user-defined cost allocation
tags in the AWS Billing and Cost Management console after the first tagged resources
have been created.

### Resource Sizing

```hcl
# Total task resources (must be valid Fargate combination)
task_cpu    = "1024"  # 1 vCPU
task_memory = "2048"  # 2 GB

# Weaviate container
weaviate_cpu    = 512   # 0.5 vCPU
weaviate_memory = 1024  # 1 GB

# Event Finder container
event_finder_cpu    = 256  # 0.25 vCPU
event_finder_memory = 512  # 0.5 GB
```

### Scheduling

```hcl
# Cron format: minute hour day month day-of-week
schedule_expression = "cron(0 9 * * ? *)"   # 9 AM UTC daily
schedule_expression = "cron(0 18 * * ? *)"  # 6 PM UTC daily
schedule_expression = "cron(0 0 * * 1 *)"   # Midnight Monday weekly
```

## 🔍 Monitoring

### View Logs

```bash
# Real-time logs
aws logs tail /ecs/london-events --follow

# Filter by container
aws logs tail /ecs/london-events --follow --filter-pattern "weaviate"
aws logs tail /ecs/london-events --follow --filter-pattern "event-finder"
```

### Check Task Status

```bash
# List running tasks
aws ecs list-tasks --cluster london-events-cluster

# Describe task
aws ecs describe-tasks --cluster london-events-cluster --tasks <task-id>
```

### View Schedule

```bash
# Check next run time
aws scheduler get-schedule --name london-events-daily-schedule
```

## 🐛 Troubleshooting

### Task Fails to Start

**Check task stopped reason:**
```bash
aws ecs describe-tasks --cluster london-events-cluster --tasks <task-id> \
  | jq '.tasks[0].stoppedReason'
```

**Common issues:**
- Image not found in ECR → Push image
- Insufficient memory → Increase `task_memory`
- No internet access → Check security groups

### Weaviate Health Check Fails

**Check Weaviate logs:**
```bash
aws logs tail /ecs/london-events --follow --filter-pattern "weaviate"
```

**Common issues:**
- EFS mount failed → Check EFS security group
- Insufficient memory → Increase `weaviate_memory`
- Corrupted data → Delete EFS and recreate

### Email Not Sent

**Verify SES identities:**
```bash
aws ses get-identity-verification-attributes \
  --identities londoneventsaisummary@gmail.com butler.will1@gmail.com
```

Both should show `VerificationStatus: Success`.

## 🗑️ Cleanup

```bash
terraform destroy
```

**Note:** EFS data will be deleted. Secrets Manager has a 7-day recovery window.

## 📚 Further Reading

- [AWS ECS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EFS with ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html)
- [EventBridge Scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html)
