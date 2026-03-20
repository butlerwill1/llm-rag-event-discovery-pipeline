# Secrets Manager Module - Secure storage for API keys

# OpenAI API Key
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "${var.project_name}/openai-api-key"
  description = "OpenAI API key for event search"

  recovery_window_in_days = 7  # Allow recovery if accidentally deleted

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-openai-api-key"
    }
  )
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

