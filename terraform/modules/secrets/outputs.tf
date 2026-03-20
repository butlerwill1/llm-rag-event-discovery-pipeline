output "openai_api_key_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "secret_arns" {
  description = "List of all secret ARNs"
  value       = [aws_secretsmanager_secret.openai_api_key.arn]
}

