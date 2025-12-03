# Athena Module Variables
#
# Learning points:
# - Module input variables
# - Default values for optional parameters
# - Validation rules

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "database_name" {
  description = "Name of the Glue catalog database"
  type        = string
  default     = "pnl_demo_db"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket containing source data"
  type        = string
}

variable "bytes_scanned_limit" {
  description = "Maximum bytes scanned per query (cost control)"
  type        = number
  default     = 10737418240  # 10 GB - prevents runaway costs
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
