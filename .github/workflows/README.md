# GitHub Actions Workflows

This directory contains automated workflows for the London Events AI Agent.

## 📋 Workflows

### 1. **deploy.yml** - Docker Image Deployment
**Triggers:** Push to `main` branch (application code changes)

**What it does:**
- Builds Docker image from Dockerfile
- Pushes image to AWS ECR with two tags:
  - `<commit-sha>` - Specific version (e.g., `a3f2b1c`)
  - `latest` - Most recent version
- ECS scheduled task automatically uses the latest image

**Required secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---

### 2. **terraform-check.yml** - Terraform Validation
**Triggers:** Push or PR that changes `terraform/` files

**What it does:**
- Validates Terraform syntax
- Checks formatting
- Ensures configuration is valid

**Does NOT apply changes** - Terraform is run manually

---

### 3. **manual-run.yml** - Manual ECS Task Trigger
**Triggers:** Manual button click in GitHub Actions UI

**What it does:**
- Triggers an immediate ECS task run
- Useful for testing without waiting for the daily schedule

**Required secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---

### 4. **security-scan.yml** - Security Scanning
**Triggers:** 
- Weekly (Sunday at midnight)
- Push or PR that changes `Dockerfile` or `requirements.txt`

**What it does:**
- Scans Docker image for vulnerabilities
- Checks Python dependencies for known security issues

---

## 🔐 Required GitHub Secrets

Go to: **Repository Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AWS_ACCESS_KEY_ID` | AWS access key for GitHub Actions | See setup instructions below |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | See setup instructions below |

---

## 🚀 Setup Instructions

### Step 1: Create IAM User for GitHub Actions

```bash
# Create IAM user
aws iam create-user --user-name github-actions-event-finder

# Create access key
aws iam create-access-key --user-name github-actions-event-finder
```

**Save the output** - you'll need `AccessKeyId` and `SecretAccessKey`

### Step 2: Attach Permissions

```bash
# Apply the minimal permissions policy
aws iam put-user-policy \
  --user-name github-actions-event-finder \
  --policy-name GitHubActionsECRPolicy \
  --policy-document file://terraform/github-actions-policy.json
```

### Step 3: Add Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add:
   - Name: `AWS_ACCESS_KEY_ID`, Value: (from Step 1)
   - Name: `AWS_SECRET_ACCESS_KEY`, Value: (from Step 1)

---

## 📊 Deployment Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure (Manual - Rare)                              │
└─────────────────────────────────────────────────────────────┘

1. Edit terraform/*.tf files
2. Run: terraform apply (from your laptop)
3. Infrastructure updated


┌─────────────────────────────────────────────────────────────┐
│ Application (Automated - Frequent)                          │
└─────────────────────────────────────────────────────────────┘

1. Edit main.py, config.py, etc.
2. git commit && git push
3. GitHub Actions automatically:
   ├─> Builds Docker image
   ├─> Pushes to ECR
   └─> Next scheduled run uses new image
```

---

## 🎯 Common Tasks

### Deploy Code Changes
```bash
git add .
git commit -m "Update event search logic"
git push
# GitHub Actions automatically builds and deploys
```

### Update Infrastructure
```bash
cd terraform
terraform apply
# Manual - you control when infrastructure changes
```

### Trigger Manual Test Run
1. Go to GitHub → Actions
2. Click "Manual ECS Task Run"
3. Click "Run workflow"
4. Check CloudWatch logs for results

---

## 🔍 Monitoring

- **GitHub Actions logs:** Repository → Actions tab
- **ECS task logs:** AWS CloudWatch → Log group `/ecs/london-events`
- **ECR images:** AWS ECR → `event-finder` repository

---

## 💰 Cost Impact

- **GitHub Actions:** Free (2,000 minutes/month on free tier)
- **AWS costs:** Same as before (~$3/month)
- **No additional charges** for CI/CD automation

