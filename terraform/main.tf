# Main Terraform Configuration for Azure
#
# Learning points:
# - Terraform resource blocks
# - Module composition
# - Provider configuration
# - State management

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.45"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Remote state storage in Azure Blob Storage
  backend "azurerm" {
    # Configuration provided via -backend-config or environment variables
    # resource_group_name  = "tfstate-rg"
    # storage_account_name = "pnldemotfstate"
    # container_name       = "tfstate"
    # key                  = "dev.terraform.tfstate"
  }
}

# Azure Provider Configuration
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false  # Allow deletion in dev
    }
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# Azure AD Provider (for RBAC)
provider "azuread" {}

# Random provider for unique names
provider "random" {}

# ===================
# Data Sources
# ===================

# Current Azure client configuration
data "azurerm_client_config" "current" {}

# Current subscription
data "azurerm_subscription" "current" {}

# ===================
# Resource Group
# ===================

resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.location

  tags = local.common_tags
}

# ===================
# Local Values
# ===================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = var.owner
  }

  # Generate unique suffix for globally unique names
  unique_suffix = random_string.suffix.result
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ===================
# Networking Module
# ===================

module "networking" {
  source = "./modules/networking"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  project_name        = var.project_name

  vnet_address_space = var.vnet_address_space
  aks_subnet_prefix  = var.aks_subnet_prefix
  db_subnet_prefix   = var.db_subnet_prefix

  tags = local.common_tags
}

# ===================
# Azure Container Registry
# ===================

module "acr" {
  source = "./modules/acr"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  project_name        = var.project_name
  unique_suffix       = local.unique_suffix

  sku = var.acr_sku

  tags = local.common_tags
}

# ===================
# Azure Kubernetes Service
# ===================

module "aks" {
  source = "./modules/aks"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  project_name        = var.project_name

  kubernetes_version = var.kubernetes_version
  node_count         = var.aks_node_count
  node_vm_size       = var.aks_node_vm_size
  subnet_id          = module.networking.aks_subnet_id

  acr_id = module.acr.acr_id

  tags = local.common_tags
}

# ===================
# Azure PostgreSQL
# ===================

module "postgres" {
  source = "./modules/postgres"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  project_name        = var.project_name
  unique_suffix       = local.unique_suffix

  sku_name         = var.postgres_sku
  storage_mb       = var.postgres_storage_mb
  subnet_id        = module.networking.db_subnet_id
  private_dns_zone_id = module.networking.postgres_private_dns_zone_id

  administrator_login = var.postgres_admin_user
  database_name       = var.postgres_database_name

  tags = local.common_tags
}

# ===================
# Azure Key Vault
# ===================

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}${local.unique_suffix}kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  soft_delete_retention_days = 7
  purge_protection_enabled   = var.environment == "prod"

  # Access policy for Terraform service principal
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge"
    ]
  }

  tags = local.common_tags
}

# Store PostgreSQL connection string in Key Vault
resource "azurerm_key_vault_secret" "postgres_connection_string" {
  name         = "postgres-connection-string"
  value        = module.postgres.connection_string
  key_vault_id = azurerm_key_vault.main.id
}

# ===================
# Log Analytics Workspace
# ===================

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30

  tags = local.common_tags
}
