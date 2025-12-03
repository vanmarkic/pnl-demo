# Azure PostgreSQL Flexible Server Module
#
# Learning points:
# - Managed PostgreSQL service
# - Private networking with VNet integration
# - High availability configuration
# - Backup and retention policies

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

variable "sku_name" {
  type = string
}

variable "storage_mb" {
  type = number
}

variable "subnet_id" {
  type = string
}

variable "private_dns_zone_id" {
  type = string
}

variable "administrator_login" {
  type      = string
  sensitive = true
}

variable "database_name" {
  type = string
}

variable "tags" {
  type = map(string)
}

# ===================
# Random Password
# ===================

resource "random_password" "postgres" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}:?"
}

# ===================
# PostgreSQL Flexible Server
# ===================

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "${var.project_name}-${var.unique_suffix}-postgres"
  resource_group_name = var.resource_group_name
  location            = var.location

  # Version
  version = "15"

  # Administrator credentials
  administrator_login    = var.administrator_login
  administrator_password = random_password.postgres.result

  # Compute tier and size
  sku_name = var.sku_name

  # Storage
  storage_mb = var.storage_mb

  # Private networking
  delegated_subnet_id = var.subnet_id
  private_dns_zone_id = var.private_dns_zone_id

  # Backup configuration
  backup_retention_days        = var.environment == "prod" ? 35 : 7
  geo_redundant_backup_enabled = var.environment == "prod"

  # High availability (production only)
  # high_availability {
  #   mode                      = "ZoneRedundant"
  #   standby_availability_zone = "2"
  # }

  # Maintenance window
  maintenance_window {
    day_of_week  = 0  # Sunday
    start_hour   = 2
    start_minute = 0
  }

  tags = var.tags

  lifecycle {
    prevent_destroy = false  # Set to true for production
  }
}

# ===================
# Database
# ===================

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# ===================
# Server Configuration
# ===================

# Enable pgcrypto extension
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "PGCRYPTO,UUID-OSSP"
}

# Connection throttling
resource "azurerm_postgresql_flexible_server_configuration" "connection_throttle" {
  name      = "connection_throttle.enable"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "on"
}

# Log configuration
resource "azurerm_postgresql_flexible_server_configuration" "log_checkpoints" {
  name      = "log_checkpoints"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "on"
}

# ===================
# Firewall Rules (if needed for external access)
# ===================

# Allow Azure services (for debugging)
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  count            = var.environment == "dev" ? 1 : 0
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ===================
# Outputs
# ===================

output "server_id" {
  value = azurerm_postgresql_flexible_server.main.id
}

output "server_name" {
  value = azurerm_postgresql_flexible_server.main.name
}

output "fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "administrator_login" {
  value     = azurerm_postgresql_flexible_server.main.administrator_login
  sensitive = true
}

output "administrator_password" {
  value     = random_password.postgres.result
  sensitive = true
}

output "database_name" {
  value = azurerm_postgresql_flexible_server_database.main.name
}

output "connection_string" {
  value     = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
  sensitive = true
}
