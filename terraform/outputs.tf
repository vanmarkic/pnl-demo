# Terraform Outputs
#
# Learning points:
# - Output values for use by other systems
# - Sensitive outputs (hidden in logs)
# - Output dependencies

# ===================
# Resource Group
# ===================

output "resource_group_name" {
  description = "Name of the Azure Resource Group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the Resource Group"
  value       = azurerm_resource_group.main.location
}

# ===================
# Networking
# ===================

output "vnet_id" {
  description = "ID of the Virtual Network"
  value       = module.networking.vnet_id
}

output "aks_subnet_id" {
  description = "ID of the AKS subnet"
  value       = module.networking.aks_subnet_id
}

# ===================
# Container Registry
# ===================

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = module.acr.acr_name
}

output "acr_login_server" {
  description = "Login server URL for ACR"
  value       = module.acr.acr_login_server
}

output "acr_admin_username" {
  description = "Admin username for ACR"
  value       = module.acr.acr_admin_username
  sensitive   = true
}

# ===================
# Kubernetes Service
# ===================

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.aks.cluster_name
}

output "aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = module.aks.cluster_fqdn
}

output "aks_kube_config_command" {
  description = "Command to get AKS credentials"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.aks.cluster_name}"
}

output "aks_node_resource_group" {
  description = "Resource group containing AKS nodes"
  value       = module.aks.node_resource_group
}

# ===================
# PostgreSQL
# ===================

output "postgres_server_name" {
  description = "Name of the PostgreSQL server"
  value       = module.postgres.server_name
}

output "postgres_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = module.postgres.fqdn
}

output "postgres_connection_string" {
  description = "PostgreSQL connection string"
  value       = module.postgres.connection_string
  sensitive   = true
}

# ===================
# Key Vault
# ===================

output "key_vault_name" {
  description = "Name of the Azure Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Azure Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# ===================
# Log Analytics
# ===================

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

# ===================
# Summary
# ===================

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = <<-EOT

    ============================================
    P&L Demo Infrastructure Deployment Summary
    ============================================

    Environment: ${var.environment}
    Location: ${var.location}

    Resource Group: ${azurerm_resource_group.main.name}

    Container Registry:
      Name: ${module.acr.acr_name}
      Login: ${module.acr.acr_login_server}

    Kubernetes (AKS):
      Cluster: ${module.aks.cluster_name}
      Get credentials: az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.aks.cluster_name}

    PostgreSQL:
      Server: ${module.postgres.server_name}
      FQDN: ${module.postgres.fqdn}

    Key Vault: ${azurerm_key_vault.main.name}

    Next Steps:
    1. Get AKS credentials
    2. Push Docker images to ACR
    3. Deploy Kubernetes manifests
    4. Configure DNS/Ingress

    ============================================
  EOT
}
