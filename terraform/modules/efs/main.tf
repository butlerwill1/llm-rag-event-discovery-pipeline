# EFS Module - Persistent storage for Weaviate data

# EFS File System
resource "aws_efs_file_system" "weaviate" {
  creation_token = "${var.project_name}-weaviate-data"
  encrypted      = true

  # Performance mode
  performance_mode = "generalPurpose"  # or "maxIO" for higher throughput
  throughput_mode  = "bursting"        # or "provisioned" for consistent throughput

  # Lifecycle policy to transition files to IA storage class (cost optimization)
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-weaviate-efs"
    }
  )
}

# Security Group for EFS
resource "aws_security_group" "efs" {
  name        = "${var.project_name}-efs-sg"
  description = "Security group for EFS mount targets"
  vpc_id      = var.vpc_id

  # Allow NFS traffic from ECS tasks
  ingress {
    description     = "NFS from ECS tasks"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-efs-sg"
    }
  )
}

# EFS Mount Targets (one per subnet for high availability)
resource "aws_efs_mount_target" "weaviate" {
  count = length(var.subnet_ids)

  file_system_id  = aws_efs_file_system.weaviate.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
}

# EFS Access Point (optional - provides a specific entry point)
resource "aws_efs_access_point" "weaviate" {
  file_system_id = aws_efs_file_system.weaviate.id

  root_directory {
    path = "/weaviate"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  posix_user {
    gid = 1000
    uid = 1000
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-weaviate-access-point"
    }
  )
}

