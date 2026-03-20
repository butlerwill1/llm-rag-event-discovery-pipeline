variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
}

variable "cluster_arn" {
  description = "ARN of the ECS cluster"
  type        = string
}

variable "task_definition_arn" {
  description = "ARN of the task definition"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for task execution"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs for task execution"
  type        = list(string)
}

variable "assign_public_ip" {
  description = "Assign public IP to tasks"
  type        = bool
  default     = false
}

variable "task_execution_role_arn" {
  description = "ARN of task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of task role"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

