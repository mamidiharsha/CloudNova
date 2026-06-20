# CloudNova — Storage Services Guide

## Overview

CloudNova provides three storage services to meet different workload requirements:

1. **CloudVault** — Object storage for unstructured data
2. **BlockStore** — High-performance block storage for instances
3. **ArchiveVault** — Low-cost archival storage

## CloudVault (Object Storage)

### Features
- Unlimited storage capacity
- 99.999999999% (11 nines) data durability
- 99.99% availability SLA
- Built-in versioning and lifecycle management
- Server-side encryption (AES-256) enabled by default
- Cross-region replication available

### Storage Classes
| Class | Use Case | Retrieval Time | Price/GB/month |
|-------|----------|----------------|----------------|
| Standard | Frequently accessed data | Immediate | $0.023 |
| Infrequent Access | Monthly access patterns | Immediate | $0.0125 |
| Archive | Rarely accessed data | 1-5 hours | $0.004 |
| Deep Archive | Compliance/regulatory | 12-48 hours | $0.00099 |

### CLI Operations
```bash
# Create a bucket
cloudnova vault create my-bucket --region us-east-1

# Upload a file
cloudnova vault upload my-bucket/data/report.pdf ./report.pdf

# Download a file
cloudnova vault download my-bucket/data/report.pdf ./local-report.pdf

# List bucket contents
cloudnova vault list my-bucket

# Enable versioning
cloudnova vault versioning enable my-bucket

# Set lifecycle policy (move to archive after 90 days)
cloudnova vault lifecycle set my-bucket --transition-days 90 --target-class archive
```

### Access Control
- **Bucket Policies**: JSON-based policies for fine-grained access control
- **Access Control Lists (ACLs)**: Legacy method, use bucket policies instead
- **Pre-signed URLs**: Temporary access for external users (expires in 1-24 hours)

## BlockStore (Block Storage)

### Volume Types
| Type | IOPS | Throughput | Use Case |
|------|------|------------|----------|
| SSD General (gp3) | 3,000-16,000 | 125-1,000 MB/s | General workloads |
| SSD Performance (io2) | Up to 64,000 | Up to 4,000 MB/s | Databases, latency-sensitive |
| HDD Throughput (st1) | Up to 500 | Up to 500 MB/s | Big data, log processing |
| HDD Cold (sc1) | Up to 250 | Up to 250 MB/s | Infrequent access |

### Snapshots
- Point-in-time backups of BlockStore volumes
- Stored in CloudVault (charged at snapshot rate)
- Can be used to create new volumes or restore data
- **Automated snapshots**: Configure at **Storage → Snapshots → Schedule**
- Recommended: Daily snapshots with 30-day retention

### Troubleshooting Storage

#### Volume Not Attaching
1. Verify the volume and instance are in the **same availability zone**
2. Check that the instance is in `running` or `stopped` state
3. Verify the device name is not already in use: `cloudnova blockstore describe-attachments --instance-id <ID>`
4. Check quota limits: **Settings → Quotas → Storage**

#### Performance Issues
1. Check IOPS consumption: **Monitoring → Storage Metrics → IOPS**
2. Ensure you're using the correct volume type for your workload
3. For gp3 volumes, verify provisioned IOPS is sufficient
4. Consider upgrading from gp3 to io2 for database workloads
5. Enable burst balance monitoring for gp3 volumes
