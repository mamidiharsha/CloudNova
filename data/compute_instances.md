# CloudNova — Compute Instances Guide

## Instance Types Overview

CloudNova offers a range of compute instances optimized for different workloads:

### General Purpose (cn-standard)
Balanced compute, memory, and networking. Ideal for web servers, development environments, and small databases.

| Instance | vCPUs | RAM | Storage | Network |
|----------|-------|-----|---------|---------|
| cn-standard-1 | 1 | 2 GB | 20 GB SSD | Up to 1 Gbps |
| cn-standard-2 | 2 | 4 GB | 40 GB SSD | Up to 2 Gbps |
| cn-standard-4 | 4 | 8 GB | 80 GB SSD | Up to 5 Gbps |
| cn-standard-8 | 8 | 16 GB | 160 GB SSD | Up to 10 Gbps |

### Compute Optimized (cn-performance)
High-performance processors for compute-intensive tasks, batch processing, and machine learning inference.

| Instance | vCPUs | RAM | Storage | Network |
|----------|-------|-----|---------|---------|
| cn-performance-4 | 4 | 16 GB | 100 GB NVMe | Up to 10 Gbps |
| cn-performance-8 | 8 | 32 GB | 200 GB NVMe | Up to 25 Gbps |
| cn-performance-16 | 16 | 64 GB | 400 GB NVMe | Up to 25 Gbps |

### GPU Instances (cn-gpu)
For machine learning training, rendering, and scientific computing.

| Instance | GPUs | vCPUs | RAM | GPU Memory |
|----------|------|-------|-----|------------|
| cn-gpu-t4 | 1x T4 | 4 | 16 GB | 16 GB |
| cn-gpu-v100 | 1x V100 | 8 | 64 GB | 32 GB |
| cn-gpu-a100 | 1x A100 | 16 | 128 GB | 80 GB |

## Auto-Scaling

### Configuration
Auto-scaling automatically adjusts the number of instances based on demand:

1. Go to **Compute → Auto-Scaling Groups → Create**
2. Define scaling policies:
   - **Target tracking**: Maintain CPU utilization at 70%
   - **Step scaling**: Add 2 instances when CPU > 80%, remove 1 when CPU < 30%
   - **Scheduled scaling**: Scale up during business hours (9 AM - 6 PM)
3. Set minimum and maximum instance counts
4. Configure health check grace period (default: 300 seconds)

### Auto-Scaling Best Practices
- Set the **minimum instances to 2** for high availability
- Use **warm pools** to reduce instance launch time
- Configure **cooldown periods** (default: 300 seconds) to prevent rapid scaling
- Monitor scaling events in **CloudWatch → Auto-Scaling Events**

## Instance Lifecycle

### States
| State | Description |
|-------|-------------|
| `pending` | Instance is being provisioned |
| `running` | Instance is active and billing |
| `stopping` | Instance is shutting down |
| `stopped` | Instance is stopped (no compute charges, storage still billed) |
| `terminating` | Instance is being permanently deleted |
| `terminated` | Instance has been deleted |

### Common Operations
```bash
# List all instances
cloudnova compute list

# Start a stopped instance
cloudnova compute start --instance-id cn-i-abc123

# Stop an instance (preserves data)
cloudnova compute stop --instance-id cn-i-abc123

# Terminate an instance (permanent)
cloudnova compute terminate --instance-id cn-i-abc123

# Resize an instance (requires stop first)
cloudnova compute resize --instance-id cn-i-abc123 --type cn-standard-4
```

## Troubleshooting

### Instance Won't Start
1. Check the instance status: `cloudnova compute describe --instance-id <ID>`
2. Verify your quota: **Settings → Quotas → Compute**
3. Check the region capacity: **Status → Region Health**
4. Review system logs: `cloudnova logs get --instance-id <ID>`
5. Error `InsufficientCapacity`: Try launching in a different availability zone

### High CPU Usage
1. Connect to the instance via SSH
2. Run `top` or `htop` to identify the process
3. Check CloudNova metrics: **Monitoring → Instance Metrics**
4. Consider upgrading to a larger instance type
5. Enable auto-scaling if the load is variable
