#!/bin/bash
# Setup script to create S3 bucket for Terraform state
#
# Usage:
#   ./setup-backend.sh           # S3 only (no state locking)
#   ./setup-backend.sh --with-lock  # S3 + DynamoDB (with state locking)

set -e

AWS_REGION="eu-west-1"
BUCKET_NAME="london-events-terraform-state-$(aws sts get-caller-identity --query Account --output text)"
DYNAMODB_TABLE="london-events-terraform-locks"
CREATE_DYNAMODB=false

# Check for --with-lock flag
if [[ "$1" == "--with-lock" ]]; then
  CREATE_DYNAMODB=true
fi

echo "🪣 Creating S3 bucket for Terraform state..."

# Create S3 bucket
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION \
  2>/dev/null || echo "Bucket already exists"

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "✅ S3 bucket created: $BUCKET_NAME"

# Create DynamoDB table for state locking (optional)
if [ "$CREATE_DYNAMODB" = true ]; then
  echo "🔒 Creating DynamoDB table for state locking..."

  aws dynamodb create-table \
    --table-name $DYNAMODB_TABLE \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION \
    2>/dev/null || echo "Table already exists"

  echo "✅ DynamoDB table created: $DYNAMODB_TABLE"
  echo ""
  echo "📝 Uncomment this in your terraform/backend.tf:"
  echo ""
  echo "terraform {"
  echo "  backend \"s3\" {"
  echo "    bucket         = \"$BUCKET_NAME\""
  echo "    key            = \"london-events/terraform.tfstate\""
  echo "    region         = \"$AWS_REGION\""
  echo "    dynamodb_table = \"$DYNAMODB_TABLE\"  # ← Uncomment this line"
  echo "    encrypt        = true"
  echo "  }"
  echo "}"
else
  echo ""
  echo "ℹ️  Skipping DynamoDB table (no state locking)"
  echo "   To enable state locking, run: ./setup-backend.sh --with-lock"
  echo ""
  echo "📝 Uncomment this in your terraform/backend.tf:"
  echo ""
  echo "terraform {"
  echo "  backend \"s3\" {"
  echo "    bucket  = \"$BUCKET_NAME\""
  echo "    key     = \"london-events/terraform.tfstate\""
  echo "    region  = \"$AWS_REGION\""
  echo "    encrypt = true"
  echo "  }"
  echo "}"
fi

