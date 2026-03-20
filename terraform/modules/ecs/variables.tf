variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "task_family" {
  description = "Family name for the task definition"
  type        = string
}

variable "task_cpu" {
  description = "Total CPU for the task"
  type        = string
}

variable "task_memory" {
  description = "Total memory for the task"
  type        = string
}

variable "weaviate_image" {
  description = "Docker image for Weaviate"
  type        = string
}

variable "weaviate_cpu" {
  description = "CPU units for Weaviate container"
  type        = number
}

variable "weaviate_memory" {
  description = "Memory for Weaviate container"
  type        = number
}

variable "event_finder_image" {
  description = "Docker image for event-finder"
  type        = string
}

variable "event_finder_cpu" {
  description = "CPU units for event-finder container"
  type        = number
}

variable "event_finder_memory" {
  description = "Memory for event-finder container"
  type        = number
}

variable "model_name" {
  description = "OpenAI model name"
  type        = string
}

variable "reasoning_effort" {
  description = "Reasoning effort level"
  type        = string
}

variable "ses_from_email" {
  description = "SES sender email"
  type        = string
}

variable "ses_to_email" {
  description = "SES recipient email"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "openai_api_key_arn" {
  description = "ARN of OpenAI API key secret"
  type        = string
}

variable "task_execution_role_arn" {
  description = "ARN of task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of task role"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for tasks"
  type        = list(string)
}

variable "assign_public_ip" {
  description = "Assign public IP to tasks"
  type        = bool
  default     = false
}

variable "efs_file_system_id" {
  description = "EFS file system ID"
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

