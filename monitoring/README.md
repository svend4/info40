# Monitoring Configuration

Monitoring and observability configuration for the AI Agent Orchestration Platform.

## Overview

The platform uses a comprehensive monitoring stack:

- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards
- **Jaeger** - Distributed tracing
- **AlertManager** - Alert routing and management

## Structure

```
monitoring/
├── grafana-dashboards/          # Grafana dashboard definitions
│   ├── platform-overview.json   # Main platform dashboard
│   ├── agent-performance.json   # Agent metrics
│   └── task-execution.json      # Task orchestration metrics
├── prometheus/                   # Prometheus configuration (to be added)
│   ├── prometheus.yml
│   ├── alerts.yml
│   └── recording_rules.yml
├── alertmanager/                # AlertManager config (to be added)
│   └── config.yml
└── README.md                    # This file
```

## Grafana Dashboards

### 1. Platform Overview

**File**: `grafana-dashboards/platform-overview.json`

**Purpose**: High-level view of the entire platform

**Metrics**:
- Total agents (active, inactive, busy)
- Tasks in progress and completed
- Request rate and response times
- Error rates (4xx, 5xx)
- Platform revenue
- Top performing agents

**Use Cases**:
- Daily operations monitoring
- Quick health checks
- Executive dashboards
- SLA monitoring

**Key Panels**:
- Agent count statistics
- HTTP request rate
- Response time (p95, p99)
- Task execution time distribution
- Error rate with alerting
- Revenue tracking
- Task status breakdown (pie chart)

### 2. Agent Performance

**File**: `grafana-dashboards/agent-performance.json`

**Purpose**: Detailed metrics for individual agents

**Metrics**:
- Task completion rate
- Success rate
- Average rating
- Total revenue
- Resource utilization (CPU, memory)
- Error rates by type
- Capability usage
- Recent reviews

**Use Cases**:
- Agent optimization
- Performance troubleshooting
- Quality assurance
- Billing verification
- Contract renewals

**Key Panels**:
- Task completion rate graph
- Success rate with threshold alerting
- Resource utilization (CPU/memory)
- Task execution time heatmap
- Error distribution
- Capability usage bar gauge
- Recent reviews table

**Variables**:
- `$agent` - Select specific agent
- `$time_range` - Adjust time aggregation

### 3. Task Execution

**File**: `grafana-dashboards/task-execution.json`

**Purpose**: Task orchestration and execution monitoring

**Metrics**:
- Pending/running/completed/failed tasks
- Task flow rate
- Decomposition time
- Subtask distribution
- Agent matching time
- Queue depth
- Task complexity and priority

**Use Cases**:
- Orchestration performance tuning
- Queue management
- Capacity planning
- Bottleneck identification

**Key Panels**:
- Task status counters
- Task flow rate (created/completed/failed)
- Decomposition performance
- Queue depth with alerting
- Execution pipeline visualization
- Task distribution by complexity/priority
- Active tasks table

**Alerts**:
- High queue depth (>100 tasks)
- Slow decomposition times
- High failure rate

## Installation

### Import Dashboards to Grafana

#### Method 1: Using Grafana UI

1. Open Grafana (default: http://localhost:3000)
2. Login (default: admin/admin)
3. Go to **Dashboards** → **Import**
4. Upload JSON file or paste JSON content
5. Select Prometheus datasource
6. Click **Import**

#### Method 2: Using Grafana API

```bash
# Set variables
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

# Import dashboard
for dashboard in grafana-dashboards/*.json; do
  curl -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -d @"$dashboard" \
    "$GRAFANA_URL/api/dashboards/db"
done
```

#### Method 3: Using Provisioning

1. Copy dashboards to Grafana provisioning directory:

```bash
# In Kubernetes
kubectl create configmap grafana-dashboards \
  --from-file=grafana-dashboards/ \
  -n agent-platform

# Mount in Grafana pod at /etc/grafana/provisioning/dashboards/
```

2. Create provisioning config:

```yaml
# /etc/grafana/provisioning/dashboards/dashboards.yaml
apiVersion: 1

providers:
  - name: 'Platform Dashboards'
    orgId: 1
    folder: 'Agent Platform'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
```

## Metrics Reference

### Platform Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agent_status` | Gauge | Agent status (active, inactive, busy, offline) |
| `task_status` | Gauge | Task status (pending, running, completed, failed) |
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | HTTP request latency |
| `tasks_completed_total` | Counter | Total completed tasks |
| `tasks_failed_total` | Counter | Total failed tasks |
| `platform_revenue_total` | Counter | Total platform revenue |

### Agent Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agent_tasks_completed_total` | Counter | Tasks completed by agent |
| `agent_tasks_total` | Counter | Total tasks assigned to agent |
| `agent_rating` | Gauge | Agent rating (0-5) |
| `agent_revenue_total` | Counter | Total revenue generated by agent |
| `agent_task_duration_seconds` | Histogram | Task execution time |
| `agent_cpu_usage` | Gauge | CPU usage percentage |
| `agent_memory_usage_bytes` | Gauge | Memory usage in bytes |
| `agent_errors_total` | Counter | Errors by type |

### Task Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `task_execution_duration_seconds` | Histogram | Total task execution time |
| `task_decomposition_duration_seconds` | Histogram | Task decomposition time |
| `task_subtask_count` | Gauge | Number of subtasks |
| `agent_matching_duration_seconds` | Histogram | Agent matching time |
| `task_queue_depth` | Gauge | Queue depth by queue name |
| `task_complexity` | Gauge | Task complexity level |
| `task_priority` | Gauge | Task priority |

## Alerting

### Alert Configuration

Alerts are defined in dashboard panels and in Prometheus `alerts.yml`.

**Critical Alerts**:
- High error rate (>10 errors/sec for 5 minutes)
- High queue depth (>100 tasks for 5 minutes)
- Service down (no heartbeat for 1 minute)
- Low success rate (<95% for 10 minutes)

**Warning Alerts**:
- Elevated error rate (>5 errors/sec for 10 minutes)
- High queue depth (>50 tasks for 10 minutes)
- Slow response times (p95 > 2s for 5 minutes)
- Low agent availability (<10 active agents)

### Alert Channels

Configure in Grafana → Alerting → Notification channels:

- **Slack** - #platform-alerts
- **Email** - ops-team@example.com
- **PagerDuty** - For critical alerts
- **Webhook** - Custom integrations

## Custom Metrics

### Adding New Metrics

1. **Instrument your code**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
task_counter = Counter(
    'my_service_tasks_total',
    'Total tasks processed',
    ['service', 'status']
)

task_duration = Histogram(
    'my_service_task_duration_seconds',
    'Task execution time',
    ['task_type']
)

# Use metrics
task_counter.labels(service='orchestrator', status='success').inc()

with task_duration.labels(task_type='data_analysis').time():
    # Execute task
    pass
```

2. **Expose metrics endpoint**:

```python
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})
```

3. **Update Prometheus scrape config**:

```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['my-service:8000']
```

4. **Create dashboard panels**:

Use the new metrics in Grafana queries:
```promql
rate(my_service_tasks_total[5m])
```

## Best Practices

### Dashboard Design

1. **Use consistent time ranges** - Default to last 6 hours
2. **Add thresholds** - Visual indicators for normal/warning/critical
3. **Use appropriate visualizations**:
   - Counters → Graph or Stat
   - Gauges → Gauge or Stat
   - Histograms → Heatmap or Graph (with percentiles)
4. **Add variables** - For filtering (service, agent, time_range)
5. **Keep it simple** - Don't overcrowd dashboards

### Metric Naming

Follow Prometheus naming conventions:

- Use snake_case
- Include unit suffix: `_seconds`, `_bytes`, `_total`
- Use meaningful labels
- Keep cardinality low

Examples:
- `http_request_duration_seconds` ✅
- `httpRequestTime` ❌
- `agent_tasks_completed_total{agent_id="123", status="success"}` ✅

### Query Optimization

1. **Use recording rules** for expensive queries
2. **Limit time ranges** in queries
3. **Use rate() for counters** instead of raw values
4. **Aggregate before querying** when possible

```promql
# Good - aggregated
sum(rate(http_requests_total[5m])) by (service)

# Bad - high cardinality
rate(http_requests_total[5m])
```

## Troubleshooting

### Dashboard Not Loading

1. Check Prometheus datasource connection
2. Verify metrics are being scraped: `http://prometheus:9090/targets`
3. Test query in Prometheus UI
4. Check Grafana logs: `kubectl logs -f deployment/grafana`

### Missing Data

1. Verify service is exposing `/metrics` endpoint
2. Check Prometheus scrape config
3. Verify network connectivity
4. Check for label mismatches

### Slow Queries

1. Reduce time range
2. Use recording rules
3. Increase Prometheus resources
4. Optimize query (use rate, aggregations)

## Advanced Features

### Template Variables

Dynamic dashboards with variables:

```json
{
  "templating": {
    "list": [
      {
        "name": "service",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(http_requests_total, service)",
        "multi": true,
        "includeAll": true
      }
    ]
  }
}
```

Use in queries: `rate(http_requests_total{service=~"$service"}[5m])`

### Annotations

Mark events on graphs:

```json
{
  "annotations": {
    "list": [
      {
        "datasource": "Prometheus",
        "expr": "ALERTS{alertstate=\"firing\"}",
        "titleFormat": "Alert: {{alertname}}",
        "iconColor": "red"
      }
    ]
  }
}
```

### Recording Rules

Pre-compute expensive queries:

```yaml
# prometheus/recording_rules.yml
groups:
  - name: agent_rules
    interval: 30s
    rules:
      - record: agent:task_success_rate:5m
        expr: |
          rate(agent_tasks_completed_total{status="success"}[5m])
          / rate(agent_tasks_total[5m])
```

## Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

**Happy Monitoring!** 📊
