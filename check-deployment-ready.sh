#!/bin/bash
# Pre-flight check before triggering GitHub Actions

set -e

AWS_REGION="eu-west-1"
ECR_REPO="event-finder"
IAM_USER="github-actions-event-finder"
CLUSTER_NAME="london-events-cluster"

echo "🔍 Pre-Flight Check for GitHub Actions Deployment"
echo "=================================================="
echo ""

ERRORS=0
WARNINGS=0

# Check 1: AWS CLI configured
echo "1️⃣  Checking AWS CLI..."
if aws sts get-caller-identity &>/dev/null; then
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  echo "   ✅ AWS CLI configured (Account: $ACCOUNT_ID)"
else
  echo "   ❌ AWS CLI not configured"
  ((ERRORS++))
fi
echo ""

# Check 2: ECR Repository exists
echo "2️⃣  Checking ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION &>/dev/null; then
  ECR_URL=$(aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)
  echo "   ✅ ECR repository exists: $ECR_URL"
else
  echo "   ❌ ECR repository NOT found"
  echo "      Run: cd terraform && terraform apply"
  ((ERRORS++))
fi
echo ""

# Check 3: ECS Cluster exists
echo "3️⃣  Checking ECS cluster..."
if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
  echo "   ✅ ECS cluster exists and is ACTIVE"
else
  echo "   ❌ ECS cluster NOT found or not active"
  echo "      Run: cd terraform && terraform apply"
  ((ERRORS++))
fi
echo ""

# Check 4: IAM User exists
echo "4️⃣  Checking IAM user for GitHub Actions..."
if aws iam get-user --user-name $IAM_USER &>/dev/null; then
  echo "   ✅ IAM user exists: $IAM_USER"
  
  # Check if user has policies
  POLICIES=$(aws iam list-user-policies --user-name $IAM_USER --query 'PolicyNames' --output text)
  if [[ -n "$POLICIES" ]]; then
    echo "   ✅ IAM policies attached: $POLICIES"
  else
    echo "   ⚠️  No inline policies attached"
    echo "      Run: aws iam put-user-policy --user-name $IAM_USER --policy-name GitHubActionsECRPolicy --policy-document file://terraform/github-actions-policy.json"
    ((WARNINGS++))
  fi
else
  echo "   ❌ IAM user NOT found"
  echo "      Run: aws iam create-user --user-name $IAM_USER"
  echo "      Then: aws iam create-access-key --user-name $IAM_USER"
  ((ERRORS++))
fi
echo ""

# Check 5: Secrets Manager secret exists
echo "5️⃣  Checking Secrets Manager..."
if aws secretsmanager describe-secret --secret-id london-events/openai-api-key --region $AWS_REGION &>/dev/null; then
  echo "   ✅ OpenAI API key secret exists"
else
  echo "   ❌ OpenAI API key secret NOT found"
  echo "      Run: cd terraform && terraform apply"
  ((ERRORS++))
fi
echo ""

# Check 6: Workflow file exists
echo "6️⃣  Checking GitHub Actions workflow..."
if [ -f ".github/workflows/deploy.yml" ]; then
  echo "   ✅ deploy.yml workflow file exists"
else
  echo "   ❌ deploy.yml NOT found"
  ((ERRORS++))
fi
echo ""

# Check 7: Dockerfile exists
echo "7️⃣  Checking Dockerfile..."
if [ -f "Dockerfile" ]; then
  echo "   ✅ Dockerfile exists"
else
  echo "   ❌ Dockerfile NOT found"
  ((ERRORS++))
fi
echo ""

# Check 8: Git repository
echo "8️⃣  Checking Git repository..."
if git rev-parse --git-dir &>/dev/null; then
  BRANCH=$(git branch --show-current)
  echo "   ✅ Git repository initialized (branch: $BRANCH)"
  
  if [ "$BRANCH" != "main" ]; then
    echo "   ⚠️  Not on 'main' branch (workflow triggers on 'main')"
    ((WARNINGS++))
  fi
  
  # Check for uncommitted changes
  if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "   ⚠️  You have uncommitted changes"
    ((WARNINGS++))
  fi
else
  echo "   ❌ Not a Git repository"
  ((ERRORS++))
fi
echo ""

# Check 9: GitHub remote
echo "9️⃣  Checking GitHub remote..."
if git remote get-url origin &>/dev/null; then
  REMOTE=$(git remote get-url origin)
  echo "   ✅ GitHub remote configured: $REMOTE"
else
  echo "   ❌ No GitHub remote configured"
  echo "      Run: git remote add origin <your-repo-url>"
  ((ERRORS++))
fi
echo ""

# Summary
echo "=================================================="
echo "📊 Summary"
echo "=================================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo "✅ All checks passed! Ready to push to GitHub."
  echo ""
  echo "🚀 Next steps:"
  echo "   1. Commit your changes: git add . && git commit -m 'Setup GitHub Actions'"
  echo "   2. Push to GitHub: git push origin main"
  echo "   3. Watch the workflow: Go to GitHub → Actions tab"
elif [ $ERRORS -eq 0 ]; then
  echo "⚠️  $WARNINGS warning(s) found, but you can proceed"
  echo ""
  echo "🚀 You can push to GitHub, but review warnings above"
else
  echo "❌ $ERRORS error(s) found. Fix these before pushing:"
  echo ""
  echo "   Review the ❌ items above and fix them first"
  exit 1
fi

