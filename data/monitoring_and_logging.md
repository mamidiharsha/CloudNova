# CloudNova — Monitoring and Logging Guide

## CloudWatch (Monitoring Service)

### Overview
CloudWatch provides real-time monitoring for all CloudNova resources with metrics, dashboards, alarms, and automated actions.

### Default Metrics
All compute instances automatically report these metrics at 5-minute intervals:

| Metric | Description | Unit |
|--------|-------------|------|
| CPUUtilization | CPU usage percentage | Percent |
| MemoryUtilization | RAM usage percentage | Percent |
| DiskReadOps | Disk read operations | Count |
| DiskWriteOps | Disk write operations | Count |
| NetworkIn | Incoming network bytes | Bytes |
| NetworkOut | Outgoing network bytes | Bytes |
| StatusCheckFailed | System/instance status | Boolean |

### Custom Metrics
Push custom application metrics using the CloudWatch API:
```bash
cloudnova monitoring put-metric \
  --namespace MyApp \
  --metric-name RequestLatency \
  --value 125 \
  --unit Milliseconds
```

### Setting Up Alarms
1. Go to **Monitoring → Alarms → Create Alarm**
2. Select metric and resource
3. Define threshold (e.g., CPUUtilization > 80% for 5 minutes)
4. Configure notification channels:
   - **Email** (via SNS topic)
   - **Slack** (webhook integration)
   - **PagerDuty** (API integration)
   - **SMS** (Business and Enterprise tiers)
5. Optionally configure auto-scaling actions

### Alarm States
| State | Description |
|-------|-------------|
| `OK` | Metric is within defined thresholds |
| `ALARM` | Metric has breached the threshold |
| `INSUFFICIENT_DATA` | Not enough data to evaluate |

## Log Aggregation (CloudLogs)

### Log Groups and Streams
- **Log Group**: Container for related log streams (e.g., `/app/production/web-server`)
- **Log Stream**: Sequence of log events from a single source

### Sending Logs
Install the CloudNova Logging Agent:
```bash
# Install agent
cloudnova agent install --type logging

# Configure log sources (edit /etc/cloudnova/logging-agent.yaml)
log_sources:
  - name: application
    path: /var/log/app/*.log
    log_group: /app/production/web-server
  - name: system
    path: /var/log/syslog
    log_group: /system/production
```

### Log Querying
```bash
# Search logs
cloudnova logs search --group /app/production/web-server --query "ERROR" --since 1h

# Filter by pattern
cloudnova logs search --group /app/production --query '{ $.statusCode >= 500 }' --since 24h

# Export logs
cloudnova logs export --group /app/production --since 7d --format json --destination my-vault-bucket/logs/
```

### Log Retention
| Retention Period | Monthly Cost/GB |
|------------------|-----------------|
| 1 day | $0.50 |
| 7 days | $0.50 |
| 30 days | $0.50 |
| 90 days | $0.25 |
| 1 year | $0.10 |
| Indefinite | $0.03 |

## Dashboards

### Creating a Dashboard
1. Navigate to **Monitoring → Dashboards → Create**
2. Add widgets:
   - **Line Chart**: CPU, memory, network trends
   - **Number**: Current metric values
   - **Gauge**: Utilization percentages
   - **Log Table**: Recent errors and warnings
   - **Alarm Status**: Overview of all alarm states
3. Set auto-refresh interval (10s, 30s, 1m, 5m)
4. Share dashboards with team members

### Pre-built Dashboard Templates
- **Infrastructure Overview**: CPU, memory, disk, network for all instances
- **Application Performance**: Request rate, latency, error rate
- **Cost Monitor**: Daily spend, top resources, budget tracking
- **Security Audit**: Failed login attempts, API anomalies

## Troubleshooting Monitoring Issues

### Metrics Not Appearing
1. Verify the CloudNova monitoring agent is running: `systemctl status cloudnova-agent`
2. Check agent logs: `/var/log/cloudnova/agent.log`
3. Verify IAM permissions include `monitoring:PutMetricData`
4. Ensure network connectivity to the CloudNova monitoring endpoint
5. Check if the metric namespace and dimensions are correct

### Alarm Not Triggering
1. Verify the alarm threshold and evaluation period
2. Check the metric data points: **Monitoring → Metrics → Graph**
3. Ensure the alarm is in `OK` state (not `INSUFFICIENT_DATA`)
4. Verify notification channel configuration (SNS topic, email subscription)
5. Check for alarm suppression rules
