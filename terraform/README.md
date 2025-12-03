# Terraform Infrastructure for Azure

This directory contains Terraform configurations for deploying the P&L Demo infrastructure on Azure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Resource Group                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Azure          │    │  Azure          │                     │
│  │  Container      │    │  Kubernetes     │                     │
│  │  Registry       │───▶│  Service (AKS)  │                     │
│  │  (ACR)          │    │                 │                     │
│  └─────────────────┘    └────────┬────────┘                     │
│                                  │                               │
│                         ┌────────▼────────┐                     │
│                         │   Virtual       │                     │
│                         │   Network       │                     │
│                         │   (VNet)        │                     │
│                         └────────┬────────┘                     │
│                                  │                               │
│  ┌─────────────────┐    ┌────────▼────────┐                     │
│  │  Azure          │    │  Azure          │                     │
│  │  PostgreSQL     │◀───│  Private        │                     │
│  │  Flexible       │    │  Endpoint       │                     │
│  │  Server         │    │                 │                     │
│  └─────────────────┘    └─────────────────┘                     │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  Azure          │    │  Azure          │                     │
│  │  Key Vault      │    │  Monitor /      │                     │
│  │                 │    │  Log Analytics  │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. Azure CLI installed and configured
2. Terraform >= 1.6.0
3. Azure subscription with Owner access
4. Storage account for Terraform state

## Setup

### 1. Create State Storage (one-time)

```bash
# Login to Azure
az login

# Create resource group for state
az group create --name tfstate-rg --location westeurope

# Create storage account
az storage account create \
  --name pnldemotfstate \
  --resource-group tfstate-rg \
  --location westeurope \
  --sku Standard_LRS

# Create container
az storage container create \
  --name tfstate \
  --account-name pnldemotfstate
```

### 2. Initialize Terraform

```bash
cd terraform

terraform init \
  -backend-config="resource_group_name=tfstate-rg" \
  -backend-config="storage_account_name=pnldemotfstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=dev.terraform.tfstate"
```

### 3. Deploy

```bash
# Development
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"

# Production
terraform plan -var-file="environments/prod.tfvars"
terraform apply -var-file="environments/prod.tfvars"
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `aks` | Azure Kubernetes Service cluster |
| `acr` | Azure Container Registry |
| `postgres` | Azure Database for PostgreSQL Flexible Server |
| `networking` | Virtual Network, Subnets, NSGs |

## Outputs

After applying, you'll get:
- AKS cluster name and credentials command
- ACR login server URL
- PostgreSQL connection string
- Key Vault URI

## Cost Estimation (Dev)

| Resource | SKU | Monthly Cost (EUR) |
|----------|-----|-------------------|
| AKS | Standard_B2s x 2 | ~€60 |
| PostgreSQL | Burstable B1ms | ~€15 |
| ACR | Basic | ~€5 |
| VNet/NSG | - | ~€5 |
| **Total** | | **~€85** |

## Security Best Practices

- All secrets stored in Azure Key Vault
- Private endpoints for database
- Network policies enabled on AKS
- RBAC for AKS and ACR
- Encryption at rest enabled
