# Terraform Variables for London Events AI Agent
# Configure these values in terraform.tfvars or pass via command line

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "llm-rag-event-summariser"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Application Configuration
variable "openai_api_key" {
  description = "OpenAI API key (will be stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "model_name" {
  description = "OpenAI model to use for event search"
  type        = string
  default     = "gpt-5"
}

variable "reasoning_effort" {
  description = "Reasoning effort level (minimal, low, medium, high, xhigh)"
  type        = string
  default     = "medium"
}

variable "ses_from_email" {
  description = "Verified SES sender email address"
  type        = string
  default     = "londoneventsaisummary@gmail.com"
}

variable "ses_to_email" {
  description = "Email address to receive event digests"
  type        = string
  default     = "butler.will1@gmail.com"
}

# ECS Configuration
variable "weaviate_cpu" {
  description = "CPU units for Weaviate container (256 = 0.25 vCPU)"
  type        = number
  default     = 512  # 0.5 vCPU
}

variable "weaviate_memory" {
  description = "Memory for Weaviate container in MB"
  type        = number
  default     = 1024  # 1 GB
}

variable "event_finder_cpu" {
  description = "CPU units for event-finder container (256 = 0.25 vCPU)"
  type        = number
  default     = 256  # 0.25 vCPU
}

variable "event_finder_memory" {
  description = "Memory for event-finder container in MB"
  type        = number
  default     = 512  # 0.5 GB
}

# Total task CPU and memory (must be valid Fargate combination)
# Valid combinations: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
variable "task_cpu" {
  description = "Total CPU for the task (sum of all containers)"
  type        = string
  default     = "1024"  # 1 vCPU
}

variable "task_memory" {
  description = "Total memory for the task (sum of all containers)"
  type        = string
  default     = "2048"  # 2 GB
}

# Scheduling
variable "schedule_expression" {
  description = "EventBridge schedule expression (cron or rate)"
  type        = string
  default     = "cron(0 9 * * ? *)"  # 9 AM UTC daily
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b"]
}

# Tags
variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "london-events-ai"
    ManagedBy   = "terraform"
    Environment = "prod"
  }
}

# Docker Image
variable "ecr_repository_name" {
  description = "Name of the ECR repository for event-finder image"
  type        = string
  default     = "event-finder"
}

variable "event_finder_image_tag" {
  description = "Docker image tag for event-finder"
  type        = string
  default     = "latest"
}

variable "weaviate_image" {
  description = "Weaviate Docker image"
  type        = string
  default     = "semitechnologies/weaviate:1.23.7"
}



