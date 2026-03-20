variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where EFS will be created"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for EFS mount targets"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs allowed to access EFS"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

