# Terraform Outputs

output "ecr_repository_url" {
  description = "URL of the ECR repository for pushing Docker images"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = module.ecr.repository_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.ecs.task_definition_arn
}

output "task_definition_family" {
  description = "Family name of the task definition"
  value       = module.ecs.task_definition_family
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for ECS tasks"
  value       = module.ecs.log_group_name
}

output "efs_file_system_id" {
  description = "ID of the EFS file system for Weaviate data"
  value       = module.efs.file_system_id
}

output "scheduler_rule_name" {
  description = "Name of the EventBridge scheduler rule"
  value       = module.scheduler.rule_name
}

output "schedule_expression" {
  description = "Schedule expression for the EventBridge rule"
  value       = var.schedule_expression
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "deployment_instructions" {
  description = "Instructions for deploying the application"
  value = <<-EOT
    
    ╔════════════════════════════════════════════════════════════════════╗
    ║          London Events AI Agent - Deployment Complete!            ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    📦 Next Steps:
    
    1. Build and push your Docker image to ECR:
       
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.ecr.repository_url}
       
       docker build -t ${var.ecr_repository_name} .
       docker tag ${var.ecr_repository_name}:latest ${module.ecr.repository_url}:latest
       docker push ${module.ecr.repository_url}:latest
    
    2. Verify SES email addresses (if not already done):
       
       aws ses verify-email-identity --email-address ${var.ses_from_email} --region ${var.aws_region}
       aws ses verify-email-identity --email-address ${var.ses_to_email} --region ${var.aws_region}
       
       Check your email and click the verification links!
    
    3. Test the task manually (optional):

       aws ecs run-task \
         --cluster ${module.ecs.cluster_name} \
         --task-definition ${module.ecs.task_definition_family} \
         --launch-type FARGATE \
         --network-configuration "awsvpcConfiguration={subnets=[${join(",", module.vpc.public_subnet_ids)}],securityGroups=[${module.ecs.task_security_group_id}],assignPublicIp=ENABLED}"
    
    4. View logs in CloudWatch:
       
       aws logs tail ${module.ecs.log_group_name} --follow
    
    5. Monitor scheduled runs:
       
       Schedule: ${var.schedule_expression}
       Next run: Check EventBridge console
    
    📊 Resources Created:
    - ECS Cluster: ${module.ecs.cluster_name}
    - ECR Repository: ${module.ecr.repository_url}
    - EFS File System: ${module.efs.file_system_id}
    - CloudWatch Logs: ${module.ecs.log_group_name}
    - EventBridge Rule: ${module.scheduler.rule_name}
    
    💰 Estimated Monthly Cost: ~$2-5/month
    - ECS Fargate: ~$0.75/month (15 min/day)
    - EFS Storage: ~$1.50/month (5 GB)
    - Data Transfer: ~$0.50/month
    - CloudWatch Logs: ~$0.50/month
    
    🔧 Useful Commands:
    - Update task: terraform apply
    - View logs: aws logs tail ${module.ecs.log_group_name} --follow
    - Manual run: See step 3 above
    - Destroy all: terraform destroy
    
    ✅ Your AI agent will now run daily at ${var.schedule_expression}!
    
  EOT
}

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "task_security_group_id" {
  description = "Security group ID for ECS tasks"
  value       = module.ecs.task_security_group_id
}

