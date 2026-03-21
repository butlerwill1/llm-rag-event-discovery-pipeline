# ECS Module - Container orchestration

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(
    var.tags,
    {
      Name = var.cluster_name
    }
  )
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = var.log_group_name
  retention_in_days = 7 # Keep logs for 7 days (cost optimization)

  tags = merge(
    var.tags,
    {
      Name = var.log_group_name
    }
  )
}

# Security Group for ECS Tasks
resource "aws_security_group" "task" {
  name_prefix = "${var.project_name}-task-sg-"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  # Allow outbound HTTPS (for OpenAI API, AWS services)
  egress {
    description = "HTTPS to internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow outbound HTTP (for package downloads, etc.)
  egress {
    description = "HTTP to internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow communication between containers (Weaviate port)
  egress {
    description = "Weaviate port"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "Weaviate port from same security group"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    self        = true
  }

  # Allow NFS to EFS
  egress {
    description = "NFS to EFS"
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-task-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Task Definition (multi-container: Weaviate + Event Finder)
resource "aws_ecs_task_definition" "main" {
  family                   = var.task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  # Container definitions
  container_definitions = jsonencode([
    # Weaviate container
    {
      name      = "weaviate"
      image     = var.weaviate_image
      cpu       = var.weaviate_cpu
      memory    = var.weaviate_memory
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        },
        {
          containerPort = 50051
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "QUERY_DEFAULTS_LIMIT"
          value = "25"
        },
        {
          name  = "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED"
          value = "true"
        },
        {
          name  = "PERSISTENCE_DATA_PATH"
          value = "/var/lib/weaviate"
        },
        {
          name  = "DEFAULT_VECTORIZER_MODULE"
          value = "none"
        },
        {
          name  = "CLUSTER_HOSTNAME"
          value = "node1"
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "weaviate-data"
          containerPath = "/var/lib/weaviate"
          readOnly      = false
        }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "wget --spider -q http://localhost:8080/v1/.well-known/ready || exit 1"]
        interval    = 15
        timeout     = 10
        retries     = 5
        startPeriod = 90
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "weaviate"
        }
      }
    },
    # Event Finder container
    {
      name      = "event-finder"
      image     = var.event_finder_image
      cpu       = var.event_finder_cpu
      memory    = var.event_finder_memory
      essential = false # Allow task to complete when this container exits

      # Wait for Weaviate to be healthy before starting
      dependsOn = [
        {
          containerName = "weaviate"
          condition     = "HEALTHY"
        }
      ]

      environment = [
        {
          name  = "WEAVIATE_URL"
          value = "http://localhost:8080"
        },
        {
          name  = "MODEL_NAME"
          value = var.model_name
        },
        {
          name  = "REASONING_EFFORT"
          value = var.reasoning_effort
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "SES_FROM_EMAIL"
          value = var.ses_from_email
        },
        {
          name  = "SES_TO_EMAIL"
          value = var.ses_to_email
        }
      ]

      secrets = [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = var.openai_api_key_arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "event-finder"
        }
      }
    }
  ])

  # EFS volume for Weaviate data
  volume {
    name = "weaviate-data"

    efs_volume_configuration {
      file_system_id     = var.efs_file_system_id
      transit_encryption = "ENABLED"

      authorization_config {
        iam = "DISABLED"
      }
    }
  }

  tags = merge(
    var.tags,
    {
      Name = var.task_family
    }
  )
}

