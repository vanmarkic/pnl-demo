# Azure Kubernetes Service Module
#
# Learning points:
# - AKS cluster configuration
# - Node pools and VM sizing
# - RBAC and managed identities
# - Network policies
# - Integration with ACR

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

variable "kubernetes_version" {
  type = string
}

variable "node_count" {
  type = number
}

variable "node_vm_size" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "acr_id" {
  type = string
}

variable "tags" {
  type = map(string)
}

# ===================
# AKS Cluster
# ===================

resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project_name}-${var.environment}-aks"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = "${var.project_name}-${var.environment}"
  kubernetes_version  = var.kubernetes_version

  # Default node pool
  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.node_vm_size
    vnet_subnet_id      = var.subnet_id
    os_disk_size_gb     = 50
    os_disk_type        = "Managed"
    max_pods            = 30
    type                = "VirtualMachineScaleSets"

    # Enable auto-scaling (optional)
    # enable_auto_scaling = true
    # min_count           = 1
    # max_count           = 5

    # Node labels
    node_labels = {
      "nodepool-type" = "system"
      "environment"   = var.environment
    }

    tags = var.tags
  }

  # Use system-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  # Network configuration
  network_profile {
    network_plugin     = "azure"      # Azure CNI for better networking
    network_policy     = "calico"     # Enable network policies
    load_balancer_sku  = "standard"
    service_cidr       = "10.1.0.0/16"
    dns_service_ip     = "10.1.0.10"
  }

  # Enable RBAC
  role_based_access_control_enabled = true

  # Azure AD integration (optional)
  # azure_active_directory_role_based_access_control {
  #   managed = true
  #   admin_group_object_ids = [var.admin_group_id]
  # }

  # Enable Azure Policy for AKS
  azure_policy_enabled = true

  # HTTP Application Routing (for dev/test)
  http_application_routing_enabled = var.environment != "prod"

  # Auto-upgrade channel
  automatic_channel_upgrade = "patch"

  # Maintenance window
  maintenance_window {
    allowed {
      day   = "Sunday"
      hours = [2, 3, 4]
    }
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      default_node_pool[0].node_count  # Ignore if auto-scaling changes count
    ]
  }
}

# ===================
# ACR Pull Permission
# ===================

# Grant AKS permission to pull images from ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

# ===================
# Outputs
# ===================

output "cluster_id" {
  value = azurerm_kubernetes_cluster.main.id
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "cluster_fqdn" {
  value = azurerm_kubernetes_cluster.main.fqdn
}

output "node_resource_group" {
  value = azurerm_kubernetes_cluster.main.node_resource_group
}

output "kubelet_identity" {
  value = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive = true
}
