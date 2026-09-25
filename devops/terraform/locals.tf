data "aws_caller_identity" "current" {}

locals {
  bucket_name = var.frontend_bucket_name != "" ? var.frontend_bucket_name : lower("${var.project_name}-${var.environment}-frontend-${data.aws_caller_identity.current.account_id}-${var.aws_region}")
  origin_id   = "frontend-s3"
}
