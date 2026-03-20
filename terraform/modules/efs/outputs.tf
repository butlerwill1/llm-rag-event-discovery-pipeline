output "file_system_id" {
  description = "ID of the EFS file system"
  value       = aws_efs_file_system.weaviate.id
}

output "file_system_arn" {
  description = "ARN of the EFS file system"
  value       = aws_efs_file_system.weaviate.arn
}

output "access_point_id" {
  description = "ID of the EFS access point"
  value       = aws_efs_access_point.weaviate.id
}

output "access_point_arn" {
  description = "ARN of the EFS access point"
  value       = aws_efs_access_point.weaviate.arn
}

output "security_group_id" {
  description = "Security group ID for EFS"
  value       = aws_security_group.efs.id
}

