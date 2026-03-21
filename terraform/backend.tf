# Terraform Backend Configuration
#
# OPTION 1: Local Backend (Default - Simplest)
# State stored locally in terraform.tfstate file
# Good for: Solo developer, manual Terraform only
# Just comment out the S3 backend below and Terraform will use local state
#
# OPTION 2: S3 Backend (Optional - For Sharing State)
# Uncomment the block below if you want to:
# - Share state between multiple machines
# - Have backup/versioning of state
# - Use Terraform from CI/CD
#
# To enable S3 backend:
# 1. Run: ./setup-backend.sh
# 2. Uncomment the terraform block below
# 3. Run: terraform init -migrate-state

# terraform {
#   backend "s3" {
#     bucket  = "london-events-terraform-state-008768223997"
#     key     = "london-events/terraform.tfstate"
#     region  = "eu-west-1"
#     encrypt = true
#
#     # Optional: State locking (prevents concurrent modifications)
#     # Only needed if multiple people/processes run Terraform
#     # dynamodb_table = "london-events-terraform-locks"
#   }
# }

