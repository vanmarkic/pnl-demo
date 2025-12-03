# AWS Athena Module - Serverless SQL Queries on S3
#
# Learning points:
# - AWS Athena enables SQL queries on S3 data without ETL
# - Uses AWS Glue Data Catalog for table metadata
# - Pay per query (~$5/TB scanned)
# - Workgroups control query settings and cost limits
#
# Architecture:
# ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
# │   Athena     │────▶│  Glue        │────▶│  S3 Data     │
# │   Workgroup  │     │  Catalog     │     │  Bucket      │
# └──────────────┘     └──────────────┘     └──────────────┘
#         │
#         └─────────────▶ S3 Results Bucket

# ===================
# AWS Glue Catalog Database
# ===================

resource "aws_glue_catalog_database" "pnl_demo" {
  name        = var.database_name
  description = "Database for PnL Demo - stores table definitions for S3 data"

  # Optional: Configure data lake settings
  create_table_default_permission {
    permissions = ["SELECT"]

    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
}

# ===================
# S3 Bucket for Athena Results
# ===================

resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.s3_bucket_name}-athena-results"

  tags = merge(var.tags, {
    Purpose = "Athena query results storage"
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "expire-old-results"
    status = "Enabled"

    # Query results are temporary - expire after 7 days
    expiration {
      days = 7
    }

    # Also clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ===================
# Athena Workgroup
# ===================

resource "aws_athena_workgroup" "pnl_demo" {
  name        = "${var.project_name}-${var.environment}"
  description = "Workgroup for PnL Demo queries"
  state       = "ENABLED"

  configuration {
    # Enforce query result location
    enforce_workgroup_configuration = true

    # Enable CloudWatch metrics
    publish_cloudwatch_metrics_enabled = true

    # Query result configuration
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/query-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    # Cost control: Set byte limits per query
    bytes_scanned_cutoff_per_query = var.bytes_scanned_limit

    # Engine version (Athena engine version 3 uses Trino)
    engine_version {
      selected_engine_version = "AUTO"
    }
  }

  tags = var.tags
}

# ===================
# Named Queries (Saved Queries)
# ===================

# Example: Get price statistics
resource "aws_athena_named_query" "price_statistics" {
  name        = "price_statistics"
  description = "Get price statistics by commodity and year"
  workgroup   = aws_athena_workgroup.pnl_demo.name
  database    = aws_glue_catalog_database.pnl_demo.name
  query       = <<-EOT
    -- Price Statistics Query
    -- Returns min, max, avg, volatility for a commodity
    SELECT
        commodity,
        year,
        COUNT(*) as data_points,
        MIN(price) as min_price,
        MAX(price) as max_price,
        AVG(price) as avg_price,
        STDDEV(price) as price_volatility,
        APPROX_PERCENTILE(price, 0.5) as median_price
    FROM prices
    WHERE commodity = 'GAS'  -- Replace with desired commodity
      AND year = 2024        -- Replace with desired year
    GROUP BY commodity, year
  EOT
}

# Example: Daily P&L analysis
resource "aws_athena_named_query" "daily_pnl_analysis" {
  name        = "daily_pnl_analysis"
  description = "Analyze daily price changes and returns"
  workgroup   = aws_athena_workgroup.pnl_demo.name
  database    = aws_glue_catalog_database.pnl_demo.name
  query       = <<-EOT
    -- Daily P&L Analysis with Window Functions
    WITH daily_prices AS (
        SELECT
            price_date,
            price,
            LAG(price) OVER (ORDER BY price_date) as prev_price
        FROM prices
        WHERE commodity = 'GAS'  -- Replace with commodity
          AND year = 2024
          AND month = 1          -- Replace with month
    )
    SELECT
        price_date,
        price,
        prev_price,
        (price - prev_price) as price_change,
        ((price - prev_price) / prev_price * 100) as pct_change
    FROM daily_prices
    WHERE prev_price IS NOT NULL
    ORDER BY price_date
  EOT
}

# Example: Trade summary
resource "aws_athena_named_query" "trade_summary" {
  name        = "trade_summary"
  description = "Aggregated trade summary by direction"
  workgroup   = aws_athena_workgroup.pnl_demo.name
  database    = aws_glue_catalog_database.pnl_demo.name
  query       = <<-EOT
    -- Trade Summary Query
    SELECT
        direction,
        COUNT(*) as trade_count,
        SUM(quantity) as total_volume,
        AVG(price) as avg_price,
        SUM(quantity * price) as total_notional
    FROM trades
    WHERE trade_date BETWEEN TIMESTAMP '2024-01-01' AND TIMESTAMP '2024-12-31'
    GROUP BY direction
  EOT
}

# ===================
# IAM Role for Athena
# ===================

resource "aws_iam_role" "athena" {
  name = "${var.project_name}-${var.environment}-athena-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "athena.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "athena_s3_access" {
  name = "athena-s3-access"
  role = aws_iam_role.athena.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadDataBucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Sid    = "WriteResultsBucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      },
      {
        Sid    = "GlueCatalogAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartitions",
          "glue:BatchGetPartition"
        ]
        Resource = [
          "arn:aws:glue:${var.aws_region}:*:catalog",
          "arn:aws:glue:${var.aws_region}:*:database/${var.database_name}",
          "arn:aws:glue:${var.aws_region}:*:table/${var.database_name}/*"
        ]
      }
    ]
  })
}

# ===================
# IAM Policy for Application
# ===================

# Policy for the application to use Athena
resource "aws_iam_policy" "app_athena_access" {
  name        = "${var.project_name}-${var.environment}-app-athena-policy"
  description = "Policy for application to access Athena"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AthenaQueryExecution"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup",
          "athena:ListNamedQueries",
          "athena:GetNamedQuery"
        ]
        Resource = [
          aws_athena_workgroup.pnl_demo.arn,
          "arn:aws:athena:${var.aws_region}:*:workgroup/${aws_athena_workgroup.pnl_demo.name}"
        ]
      },
      {
        Sid    = "S3DataAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Sid    = "S3ResultsAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      },
      {
        Sid    = "GlueCatalogAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchGetPartition",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:CreateDatabase"
        ]
        Resource = [
          "arn:aws:glue:${var.aws_region}:*:catalog",
          "arn:aws:glue:${var.aws_region}:*:database/${var.database_name}",
          "arn:aws:glue:${var.aws_region}:*:table/${var.database_name}/*"
        ]
      }
    ]
  })

  tags = var.tags
}
