# Azure Deployment Guide

## Prerequisites

- Azure CLI installed
- Azure subscription
- Docker (for building container images)

## Quick Deploy

### 1. Login to Azure

```bash
az login
az account set --subscription <your-subscription-id>
```

### 2. Create Resource Group

```bash
az group create --name riskcanvas-rg --location eastus
```

### 3. Deploy Infrastructure

```bash
az deployment group create \
  --resource-group riskcanvas-rg \
  --template-file infra/main.bicep \
  --parameters environmentName=riskcanvas
```

### 4. Deploy Application

#### Build and Push Docker Image

```bash
# Build API image
cd apps/api
docker build -t riskcanvasapi:latest .

# Tag and push to Azure Container Registry (ACR)
# First create ACR
az acr create --resource-group riskcanvas-rg --name riskcanvasacr --sku Basic

# Login to ACR
az acr login --name riskcanvasacr

# Tag and push
docker tag riskcanvasapi:latest riskcanvasacr.azurecr.io/riskcanvasapi:latest
docker push riskcanvasacr.azurecr.io/riskcanvasapi:latest
```

#### Update Container App

```bash
az containerapp update \
  --name riskcanvas-api \
  --resource-group riskcanvas-rg \
  --image riskcanvasacr.azurecr.io/riskcanvasapi:latest
```

## Environment Variables

Configure these in Azure Portal or via CLI:

### Required for Production

- `DEMO_MODE`: Set to `false` for production
- `LLM_PROVIDER`: `foundry` or `mock`
- `ENABLE_AUTH`: `true` to enable JWT authentication

### Optional (Foundry Integration)

- `FOUNDRY_ENDPOINT`: Azure OpenAI endpoint
- `FOUNDRY_API_KEY`: Azure OpenAI API key
- `FOUNDRY_DEPLOYMENT`: Model deployment name

### Optional (Observability)

- `OTEL_ENABLED`: `true` to enable OpenTelemetry
- `OTEL_ENDPOINT`: OpenTelemetry collector endpoint

## Authentication Setup

### Enable Azure Active Directory (Entra ID)

1. Register an application in Azure AD:
   ```bash
   az ad app create --display-name RiskCanvas --sign-in-audience AzureADMyOrg
   ```

2. Set environment variable:
   ```bash
   az containerapp update \
     --name riskcanvas-api \
     --resource-group riskcanvas-rg \
     --set-env-vars ENABLE_AUTH=true AZURE_AD_TENANT_ID=<tenant-id> AZURE_AD_CLIENT_ID=<client-id>
   ```

## Monitoring

### View Logs

```bash
az containerapp logs show \
  --name riskcanvas-api \
  --resource-group riskcanvas-rg \
  --follow
```

### View Metrics

```bash
az monitor metrics list \
  --resource /subscriptions/<subscription-id>/resourceGroups/riskcanvas-rg/providers/Microsoft.App/containerApps/riskcanvas-api
```

## Scaling

### Manual Scale

```bash
az containerapp update \
  --name riskcanvas-api \
  --resource-group riskcanvas-rg \
  --min-replicas 2 \
  --max-replicas 20
```

### Auto-scale Configuration

Auto-scaling is configured in `main.bicep` based on concurrent requests.

## Cleanup

```bash
az group delete --name riskcanvas-rg --yes
```

## Alternative: Azure Functions

For serverless deployment, see `deploy-functions.md`.

## Cost Estimation

- Container Apps: ~$50-100/month (basic tier, 1-2 replicas)
- Container Registry: ~$5/month (Basic)
- Log Analytics: ~$2-10/month (depends on log volume)

Total estimated: **$60-120/month** for dev/test environment.

For production with high availability and monitoring: **$200-500/month**.
