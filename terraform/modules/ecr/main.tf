# ECR Module - Docker image registry

resource "aws_ecr_repository" "main" {
  name                 = var.repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true  # Allow deletion even with images

  # Scan images for vulnerabilities
  image_scanning_configuration {
    scan_on_push = true
  }

  # Encryption
  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = var.tags
}

# Lifecycle policy to clean up old images (cost optimization)
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

