# Main Terraform configuration for London Events AI Agent on ECS Fargate

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Configure remote state storage
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "london-events/terraform.tfstate"
  #   region = "eu-west-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  account_id = data.aws_caller_identity.current.account_id

  # Resource naming
  cluster_name       = "${var.project_name}-cluster"
  task_family        = "${var.project_name}-task"
  service_name       = "${var.project_name}-service"
  log_group_name     = "/ecs/${var.project_name}"
  ecr_repository_url = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repository_name}"

  # Common tags
  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      Name        = var.project_name
    }
  )
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  vpc_cidr           = var.vpc_cidr
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)

  tags = local.common_tags
}

# EFS for Weaviate persistent storage
module "efs" {
  source = "./modules/efs"

  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
  # Use public subnets to match ECS task location (no NAT Gateway for cost optimization)
  subnet_ids = module.vpc.public_subnet_ids

  # Allow access from ECS tasks
  allowed_security_group_ids = [module.ecs.task_security_group_id]

  tags = local.common_tags
}

# ECR Repository for event-finder image
module "ecr" {
  source = "./modules/ecr"

  repository_name = var.ecr_repository_name

  tags = local.common_tags
}

# Secrets Manager for sensitive data
module "secrets" {
  source = "./modules/secrets"

  project_name   = var.project_name
  openai_api_key = var.openai_api_key

  tags = local.common_tags
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"

  project_name   = var.project_name
  ses_from_email = var.ses_from_email
  secrets_arns   = module.secrets.secret_arns

  tags = local.common_tags
}

# ECS Cluster and Task Definition
module "ecs" {
  source = "./modules/ecs"

  project_name = var.project_name
  cluster_name = local.cluster_name
  task_family  = local.task_family

  # Task configuration
  task_cpu    = var.task_cpu
  task_memory = var.task_memory

  # Container configurations
  weaviate_image  = var.weaviate_image
  weaviate_cpu    = var.weaviate_cpu
  weaviate_memory = var.weaviate_memory

  event_finder_image  = "${local.ecr_repository_url}:${var.event_finder_image_tag}"
  event_finder_cpu    = var.event_finder_cpu
  event_finder_memory = var.event_finder_memory

  # Environment variables
  model_name       = var.model_name
  reasoning_effort = var.reasoning_effort
  ses_from_email   = var.ses_from_email
  ses_to_email     = var.ses_to_email
  aws_region       = var.aws_region

  # Secrets
  openai_api_key_arn = module.secrets.openai_api_key_arn

  # IAM
  task_execution_role_arn = module.iam.task_execution_role_arn
  task_role_arn           = module.iam.task_role_arn

  # Networking
  vpc_id           = module.vpc.vpc_id
  subnet_ids       = module.vpc.public_subnet_ids # Public subnets for internet access (no NAT Gateway)
  assign_public_ip = true                         # Required for pulling images from ECR and calling external APIs

  # EFS
  efs_file_system_id = module.efs.file_system_id

  # Logging
  log_group_name = local.log_group_name

  tags = local.common_tags
}

# EventBridge Scheduler for daily execution
module "scheduler" {
  source = "./modules/scheduler"

  project_name        = var.project_name
  schedule_expression = var.schedule_expression

  # ECS task details
  cluster_arn         = module.ecs.cluster_arn
  task_definition_arn = module.ecs.task_definition_arn
  subnet_ids          = module.vpc.public_subnet_ids # Public subnets for internet access
  security_group_ids  = [module.ecs.task_security_group_id]
  assign_public_ip    = true # Required for internet access

  # IAM
  task_execution_role_arn = module.iam.task_execution_role_arn
  task_role_arn           = module.iam.task_role_arn

  tags = local.common_tags
}
