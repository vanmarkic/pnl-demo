# Azure Container Registry Module
#
# Learning points:
# - Container registry for Docker images
# - SKU tiers (Basic, Standard, Premium)
# - Admin credentials vs Service Principal authentication

# ===================
# Variables
# ===================

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "environment" {
  type = string
}

variable "project_name" {
  type = string
}

variable "unique_suffix" {
  type = string
}

variable "sku" {
  type    = string
  default = "Basic"
}

variable "tags" {
  type = map(string)
}

# ===================
# Azure Container Registry
# ===================

resource "azurerm_container_registry" "main" {
  # ACR names must be globally unique and alphanumeric only
  name                = "${var.project_name}${var.unique_suffix}acr"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  # Enable admin account for simple authentication
  # In production, prefer managed identities or service principals
  admin_enabled = true

  # Premium SKU features (uncomment if using Premium)
  # public_network_access_enabled = false
  # zone_redundancy_enabled = true
  # georeplications {
  #   location = "northeurope"
  # }

  tags = var.tags
}

# ===================
# Outputs
# ===================

output "acr_id" {
  value = azurerm_container_registry.main.id
}

output "acr_name" {
  value = azurerm_container_registry.main.name
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  value     = azurerm_container_registry.main.admin_username
  sensitive = true
}

output "acr_admin_password" {
  value     = azurerm_container_registry.main.admin_password
  sensitive = true
}
