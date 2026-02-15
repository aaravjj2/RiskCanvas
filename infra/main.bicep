// RiskCanvas Azure Container Apps Deployment
// This Bicep template deploys the RiskCanvas API to Azure Container Apps

@description('The location for resources')
param location string = resourceGroup().location

@description('Environment name')
param environmentName string = 'riskcanvas'

@description('Container image for API')
param apiImageName string = 'riskcanvasapi:latest'

@description('Enable authentication')
param enableAuth bool = false

@description('Log Analytics Workspace ID')
param logAnalyticsWorkspaceId string = ''

// ===== Container Apps Environment =====

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${environmentName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspaceId
      }
    }
  }
}

// ===== Container App - API =====

resource apiContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${environmentName}-api'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImageName
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'DEMO_MODE'
              value: 'true'
            }
            {
              name: 'LLM_PROVIDER'
              value: 'mock'
            }
            {
              name: 'ENABLE_AUTH'
              value: string(enableAuth)
            }
            {
              name: 'OTEL_ENABLED'
              value: 'false'
            }
          ]
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
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// ===== Outputs =====

output apiUrl string = apiContainerApp.properties.configuration.ingress.fqdn
output environmentId string = containerAppEnvironment.id
