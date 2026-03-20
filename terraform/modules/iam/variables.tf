variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "ses_from_email" {
  description = "SES sender email address"
  type        = string
}

variable "secrets_arns" {
  description = "ARNs of secrets to grant access to"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

