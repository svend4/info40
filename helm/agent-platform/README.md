# AI Agent Orchestration Platform - Helm Chart

Helm chart for deploying the AI Agent Orchestration Platform to Kubernetes.

## Overview

This Helm chart deploys a complete AI agent orchestration platform with:

- **API Gateway** - Main entry point for API requests
- **Registry Service** - Agent registration and discovery
- **Marketplace Service** - Agent marketplace and rental management
- **Orchestrator Service** - Task decomposition and orchestration
- **Agent Workers** - Sandboxed agent execution environments (Kagent)
- **PostgreSQL** - Primary database
- **Redis** - Caching and session management
- **RabbitMQ** - Message queue for async tasks
- **Monitoring Stack** - Prometheus, Grafana, Jaeger

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- Storage provisioner for PersistentVolumes
- (Optional) Kagent CRDs installed for agent sandboxing
- (Optional) NGINX Ingress Controller for external access
- (Optional) cert-manager for TLS certificates

## Installation

### Quick Start

```bash
# Add the Helm repository (if published)
helm repo add agent-platform https://agent-platform.example.com/charts
helm repo update

# Install with default values
helm install my-platform agent-platform/agent-platform \
  --namespace agent-platform \
  --create-namespace
```

### Install from Local Chart

```bash
# Clone the repository
git clone https://github.com/agent-platform/agent-platform.git
cd agent-platform/helm/agent-platform

# Install the chart
helm install my-platform . \
  --namespace agent-platform \
  --create-namespace \
  --values values.yaml
```

### Custom Installation

Create a custom `my-values.yaml` file:

```yaml
global:
  environment: production
  imageRegistry: ghcr.io/your-org

# Customize services
apiGateway:
  replicaCount: 5
  resources:
    limits:
      cpu: 4000m
      memory: 4Gi

# Enable ingress
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: api-gateway
              port: 8000

# Configure secrets
secrets:
  postgresPassword: "your-secure-password"
  anthropicApiKey: "sk-ant-..."
  openaiApiKey: "sk-..."
```

Install with custom values:

```bash
helm install my-platform . \
  --namespace agent-platform \
  --create-namespace \
  --values my-values.yaml
```

## Configuration

### Core Services

| Parameter | Description | Default |
|-----------|-------------|---------|
| `apiGateway.enabled` | Enable API Gateway | `true` |
| `apiGateway.replicaCount` | Number of API Gateway replicas | `3` |
| `apiGateway.autoscaling.enabled` | Enable HPA for API Gateway | `true` |
| `apiGateway.autoscaling.minReplicas` | Min replicas for HPA | `3` |
| `apiGateway.autoscaling.maxReplicas` | Max replicas for HPA | `10` |
| `registryService.enabled` | Enable Registry Service | `true` |
| `marketplaceService.enabled` | Enable Marketplace Service | `true` |
| `orchestratorService.enabled` | Enable Orchestrator Service | `true` |
| `agentWorker.enabled` | Enable Agent Workers | `true` |
| `agentWorker.autoscaling.maxReplicas` | Max agent worker replicas | `100` |

### Database

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL | `true` |
| `postgresql.auth.database` | Database name | `agent_platform` |
| `postgresql.auth.username` | Database username | `platform_admin` |
| `postgresql.persistence.enabled` | Enable persistence | `true` |
| `postgresql.persistence.size` | PVC size | `50Gi` |
| `postgresql.resources.limits.memory` | Memory limit | `8Gi` |

### Caching & Messaging

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis | `true` |
| `redis.persistence.size` | PVC size for Redis | `10Gi` |
| `redis.config.maxmemory` | Max memory for Redis | `1gb` |
| `rabbitmq.enabled` | Enable RabbitMQ | `true` |
| `rabbitmq.persistence.size` | PVC size for RabbitMQ | `20Gi` |

### Monitoring

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.prometheus.enabled` | Enable Prometheus | `true` |
| `monitoring.grafana.enabled` | Enable Grafana | `true` |
| `monitoring.jaeger.enabled` | Enable Jaeger | `true` |

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.annotations` | Ingress annotations | See values.yaml |
| `ingress.hosts` | Ingress hosts | See values.yaml |
| `ingress.tls` | TLS configuration | See values.yaml |

### Security

| Parameter | Description | Default |
|-----------|-------------|---------|
| `security.rbac.create` | Create RBAC resources | `true` |
| `security.serviceAccount.create` | Create ServiceAccount | `true` |
| `security.networkPolicies.enabled` | Enable NetworkPolicies | `true` |
| `secrets.create` | Create secrets from values | `true` |
| `secrets.postgresPassword` | PostgreSQL password | `changeme_postgres_password` |
| `secrets.anthropicApiKey` | Anthropic API key | `""` |
| `secrets.openaiApiKey` | OpenAI API key | `""` |

## Secrets Management

### Using Existing Secrets

Instead of creating secrets from values, you can use existing Kubernetes secrets:

```yaml
secrets:
  create: false

postgresql:
  auth:
    existingSecret: "my-postgres-secret"
    secretKeys:
      adminPasswordKey: "password"

rabbitmq:
  auth:
    existingSecret: "my-rabbitmq-secret"
    secretKeys:
      passwordKey: "password"
```

### Using External Secrets Operator

```yaml
# Example with External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: platform-secrets
  namespace: agent-platform
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: platform-secrets
  data:
    - secretKey: postgres-password
      remoteRef:
        key: agent-platform/postgres
        property: password
    - secretKey: anthropic-api-key
      remoteRef:
        key: agent-platform/anthropic
        property: api_key
```

## Upgrading

### Upgrade to New Version

```bash
# Update Helm repo
helm repo update

# Upgrade release
helm upgrade my-platform agent-platform/agent-platform \
  --namespace agent-platform \
  --values my-values.yaml
```

### Rollback

```bash
# List release history
helm history my-platform -n agent-platform

# Rollback to previous version
helm rollback my-platform -n agent-platform

# Rollback to specific revision
helm rollback my-platform 2 -n agent-platform
```

## Uninstallation

```bash
# Uninstall the release
helm uninstall my-platform -n agent-platform

# Delete the namespace (warning: deletes all data)
kubectl delete namespace agent-platform
```

## Examples

### Development Environment

```bash
helm install dev-platform . \
  --namespace agent-platform-dev \
  --create-namespace \
  --set global.environment=development \
  --set postgresql.persistence.enabled=false \
  --set redis.persistence.enabled=false \
  --set monitoring.prometheus.enabled=false \
  --set apiGateway.autoscaling.enabled=false \
  --set apiGateway.replicaCount=1 \
  --set registryService.replicaCount=1 \
  --set marketplaceService.replicaCount=1 \
  --set orchestratorService.replicaCount=1
```

### Production Environment

```yaml
# production-values.yaml
global:
  environment: production
  storageClass: "fast-ssd"

# High availability
apiGateway:
  replicaCount: 5
  autoscaling:
    minReplicas: 5
    maxReplicas: 20

orchestratorService:
  replicaCount: 10
  autoscaling:
    minReplicas: 10
    maxReplicas: 50

agentWorker:
  autoscaling:
    minReplicas: 20
    maxReplicas: 200

# Database HA
postgresql:
  replication:
    enabled: true
    replicas: 3
  persistence:
    size: 200Gi

# Monitoring
monitoring:
  prometheus:
    persistence:
      size: 100Gi
  grafana:
    persistence:
      size: 20Gi

# Security
secrets:
  create: false  # Use external secrets

ingress:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "1000"
  tls:
    - secretName: platform-tls-prod
      hosts:
        - api.production.example.com
```

```bash
helm install prod-platform . \
  --namespace agent-platform-prod \
  --create-namespace \
  --values production-values.yaml
```

## Post-Installation

### Verify Installation

```bash
# Check all pods are running
kubectl get pods -n agent-platform

# Check services
kubectl get svc -n agent-platform

# Check ingress
kubectl get ingress -n agent-platform
```

### Initialize Database

```bash
# Get PostgreSQL pod name
POSTGRES_POD=$(kubectl get pod -n agent-platform -l app.kubernetes.io/component=database -o jsonpath='{.items[0].metadata.name}')

# Copy schema file to pod
kubectl cp ../../database/schema.sql $POSTGRES_POD:/tmp/schema.sql -n agent-platform

# Apply schema
kubectl exec -n agent-platform $POSTGRES_POD -- psql -U platform_admin -d agent_platform -f /tmp/schema.sql

# (Optional) Load seed data
kubectl cp ../../database/seed.sql $POSTGRES_POD:/tmp/seed.sql -n agent-platform
kubectl exec -n agent-platform $POSTGRES_POD -- psql -U platform_admin -d agent_platform -f /tmp/seed.sql
```

### Access Services

```bash
# Port forward API Gateway
kubectl port-forward -n agent-platform svc/api-gateway 8000:8000

# Test API
curl http://localhost:8000/health

# Port forward Grafana
kubectl port-forward -n agent-platform svc/grafana 3000:3000
# Access at http://localhost:3000
```

## Monitoring

### Access Grafana

```bash
# Get Grafana admin password
kubectl get secret platform-secrets -n agent-platform -o jsonpath='{.data.grafana-admin-password}' | base64 -d

# Port forward
kubectl port-forward -n agent-platform svc/grafana 3000:3000

# Open browser: http://localhost:3000
# Login with admin / <password from above>
```

### Access Prometheus

```bash
kubectl port-forward -n agent-platform svc/prometheus 9090:9090
# Open browser: http://localhost:9090
```

### Access Jaeger UI

```bash
kubectl port-forward -n agent-platform svc/jaeger 16686:16686
# Open browser: http://localhost:16686
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n agent-platform

# Check logs
kubectl logs <pod-name> -n agent-platform

# Check previous logs (if pod restarted)
kubectl logs <pod-name> -n agent-platform --previous
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl run -it --rm psql-test --image=postgres:16-alpine --restart=Never -n agent-platform -- \
  psql -h postgres -U platform_admin -d agent_platform

# Check PostgreSQL logs
kubectl logs -l app.kubernetes.io/component=database -n agent-platform
```

### Storage Issues

```bash
# Check PVCs
kubectl get pvc -n agent-platform

# Describe PVC
kubectl describe pvc <pvc-name> -n agent-platform

# Check StorageClass
kubectl get storageclass
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n agent-platform

# Check HPA status
kubectl get hpa -n agent-platform

# Describe HPA
kubectl describe hpa <hpa-name> -n agent-platform
```

## Contributing

Contributions are welcome! Please see the main repository for contribution guidelines.

## License

MIT License - See LICENSE file in the repository.

## Support

- Documentation: https://docs.agent-platform.example.com
- Issues: https://github.com/agent-platform/agent-platform/issues
- Community: https://discord.gg/agent-platform
