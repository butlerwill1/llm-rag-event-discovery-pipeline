output "schedule_arn" {
  description = "ARN of the EventBridge schedule"
  value       = aws_scheduler_schedule.main.arn
}

output "rule_name" {
  description = "Name of the EventBridge schedule"
  value       = aws_scheduler_schedule.main.name
}

output "scheduler_role_arn" {
  description = "ARN of the scheduler IAM role"
  value       = aws_iam_role.scheduler.arn
}

