# Athena Module Outputs
#
# Learning points:
# - Module outputs for composition
# - Exposing resource attributes

output "database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.pnl_demo.name
}

output "workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.pnl_demo.name
}

output "workgroup_arn" {
  description = "ARN of the Athena workgroup"
  value       = aws_athena_workgroup.pnl_demo.arn
}

output "results_bucket_name" {
  description = "Name of the S3 bucket for query results"
  value       = aws_s3_bucket.athena_results.bucket
}

output "results_bucket_arn" {
  description = "ARN of the S3 bucket for query results"
  value       = aws_s3_bucket.athena_results.arn
}

output "athena_role_arn" {
  description = "ARN of the IAM role for Athena"
  value       = aws_iam_role.athena.arn
}

output "app_policy_arn" {
  description = "ARN of the IAM policy for application Athena access"
  value       = aws_iam_policy.app_athena_access.arn
}

output "named_queries" {
  description = "Map of named query IDs"
  value = {
    price_statistics   = aws_athena_named_query.price_statistics.id
    daily_pnl_analysis = aws_athena_named_query.daily_pnl_analysis.id
    trade_summary      = aws_athena_named_query.trade_summary.id
  }
}
