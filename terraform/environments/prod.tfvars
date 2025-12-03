# Production Environment Variables
#
# Usage: terraform apply -var-file="environments/prod.tfvars"

# General
project_name = "pnldemo"
environment  = "prod"
location     = "westeurope"
owner        = "pnl-demo-team"

# Networking
vnet_address_space = ["10.10.0.0/16"]  # Different range from dev
aks_subnet_prefix  = "10.10.1.0/24"
db_subnet_prefix   = "10.10.2.0/24"

# Container Registry
acr_sku = "Standard"  # Better performance for production

# Kubernetes
kubernetes_version      = "1.28"
aks_node_count          = 3
aks_node_vm_size        = "Standard_D2s_v3"  # More powerful for production
aks_enable_auto_scaling = true
aks_min_node_count      = 3
aks_max_node_count      = 10

# PostgreSQL
postgres_sku           = "GP_Standard_D2s_v3"  # General Purpose for production
postgres_storage_mb    = 131072                # 128 GB
postgres_admin_user    = "pnladmin"
postgres_database_name = "pnl_demo"

# AWS S3 (for market data)
aws_region     = "eu-west-1"
s3_bucket_name = "pnl-demo-market-data-prod"
