// Main Bicep template for RiskCanvas deployment on Azure Container Apps
// Creates all required resources for production deployment

@description('Resource group location')
param location string = resourceGroup().location

@description('Environment name (dev/staging/prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Unique solution prefix')
@minLength(3)
@maxLength(10)
param solutionPrefix string = 'riskcanvas'

@description('Container image tags')
param apiImageTag string = 'latest'
param webImageTag string = 'latest'

@description('API container image')
param apiImage string = '${solutionPrefix}acr.azurecr.io/riskcanvas-api:${apiImageTag}'

@description('Web container image')
param webImage string = '${solutionPrefix}acr.azurecr.io/riskcanvas-web:${webImageTag}'

@description('Enable Entra ID authentication')
param enableEntraAuth bool = false

@description('Azure AD Tenant ID (required if enableEntraAuth=true)')
param azureTenantId string = ''

@description('Azure AD Client ID (required if enableEntraAuth=true)')
param azureClientId string = ''

// Variables
var uniqueSuffix = uniqueString(resourceGroup().id)
var containerAppEnvName = '${solutionPrefix}-env-${environment}-${uniqueSuffix}'
var apiAppName = '${solutionPrefix}-api-${environment}'
var webAppName = '${solutionPrefix}-web-${environment}'
var acrName = '${solutionPrefix}acr${uniqueSuffix}'
var logAnalyticsName = '${solutionPrefix}-logs-${environment}'
var appInsightsName = '${solutionPrefix}-insights-${environment}'
var storageName = '${solutionPrefix}st${uniqueSuffix}'

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Storage Account (for report bundles, optional)
resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
  }
}

// Container App Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// API Container App
resource apiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: apiAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8090
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
        {
          name: 'appinsights-key'
          value: appInsights.properties.InstrumentationKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: [
            {
              name: 'DEMO_MODE'
              value: 'false'
            }
            {
              name: 'AUTH_MODE'
              value: enableEntraAuth ? 'entra' : 'none'
            }
            {
              name: 'AZURE_TENANT_ID'
              value: azureTenantId
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: azureClientId
            }
            {
              name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
              secretRef: 'appinsights-key'
            }
          ]
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Web Container App (static site via nginx)
resource webApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: webAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: webImage
          env: [
            {
              name: 'API_URL'
              value: 'https://${apiApp.properties.configuration.ingress.fqdn}'
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
    }
  }
}

// Outputs
output apiUrl string = 'https://${apiApp.properties.configuration.ingress.fqdn}'
output webUrl string = 'https://${webApp.properties.configuration.ingress.fqdn}'
output acrLoginServer string = acr.properties.loginServer
output containerAppEnvId string = containerAppEnv.id
