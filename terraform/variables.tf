# Terraform Variables
#
# Learning points:
# - Variable types (string, number, bool, list, map)
# - Default values
# - Validation rules
# - Sensitive variables

# ===================
# General
# ===================

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "pnldemo"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,10}$", var.project_name))
    error_message = "Project name must be 3-11 lowercase alphanumeric characters starting with a letter."
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "westeurope"
}

variable "owner" {
  description = "Owner of the resources (for tagging)"
  type        = string
  default     = "pnl-demo-team"
}

# ===================
# Networking
# ===================

variable "vnet_address_space" {
  description = "Address space for the Virtual Network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "aks_subnet_prefix" {
  description = "Address prefix for AKS subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "db_subnet_prefix" {
  description = "Address prefix for database subnet"
  type        = string
  default     = "10.0.2.0/24"
}

# ===================
# Azure Container Registry
# ===================

variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

# ===================
# Azure Kubernetes Service
# ===================

variable "kubernetes_version" {
  description = "Kubernetes version for AKS"
  type        = string
  default     = "1.28"
}

variable "aks_node_count" {
  description = "Number of nodes in the AKS default node pool"
  type        = number
  default     = 2

  validation {
    condition     = var.aks_node_count >= 1 && var.aks_node_count <= 10
    error_message = "Node count must be between 1 and 10."
  }
}

variable "aks_node_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_B2s"
}

variable "aks_enable_auto_scaling" {
  description = "Enable auto-scaling for AKS node pool"
  type        = bool
  default     = false
}

variable "aks_min_node_count" {
  description = "Minimum node count for auto-scaling"
  type        = number
  default     = 1
}

variable "aks_max_node_count" {
  description = "Maximum node count for auto-scaling"
  type        = number
  default     = 5
}

# ===================
# PostgreSQL
# ===================

variable "postgres_sku" {
  description = "SKU for PostgreSQL Flexible Server"
  type        = string
  default     = "B_Standard_B1ms"  # Burstable tier, cheapest option
}

variable "postgres_storage_mb" {
  description = "Storage size in MB for PostgreSQL"
  type        = number
  default     = 32768  # 32 GB
}

variable "postgres_admin_user" {
  description = "Administrator username for PostgreSQL"
  type        = string
  default     = "pnladmin"
  sensitive   = true
}

variable "postgres_database_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "pnl_demo"
}

# ===================
# AWS S3 (for market data)
# ===================

variable "aws_region" {
  description = "AWS region for S3 bucket"
  type        = string
  default     = "eu-west-1"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for market data"
  type        = string
  default     = "pnl-demo-market-data"
}
