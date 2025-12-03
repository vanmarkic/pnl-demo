# Development Environment Variables
#
# Usage: terraform apply -var-file="environments/dev.tfvars"

# General
project_name = "pnldemo"
environment  = "dev"
location     = "westeurope"
owner        = "pnl-demo-team"

# Networking
vnet_address_space = ["10.0.0.0/16"]
aks_subnet_prefix  = "10.0.1.0/24"
db_subnet_prefix   = "10.0.2.0/24"

# Container Registry
acr_sku = "Basic"

# Kubernetes
kubernetes_version = "1.28"
aks_node_count     = 2
aks_node_vm_size   = "Standard_B2s"  # Burstable, cost-effective for dev

# PostgreSQL
postgres_sku           = "B_Standard_B1ms"  # Burstable, cheapest tier
postgres_storage_mb    = 32768              # 32 GB
postgres_admin_user    = "pnladmin"
postgres_database_name = "pnl_demo"

# AWS S3 (for market data)
aws_region     = "eu-west-1"
s3_bucket_name = "pnl-demo-market-data-dev"
