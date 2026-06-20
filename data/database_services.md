# CloudNova — Database Services Guide

## Managed Database Service (CloudDB)

### Supported Engines
| Engine | Versions | Use Case |
|--------|----------|----------|
| PostgreSQL | 14, 15, 16 | General purpose, JSONB, full-text search |
| MySQL | 8.0, 8.4 | Web applications, WordPress, e-commerce |
| MongoDB | 6.0, 7.0 | Document storage, flexible schemas |
| Redis | 7.0, 7.2 | Caching, session storage, real-time analytics |

### Instance Classes
| Class | vCPUs | RAM | Storage | Price/hr |
|-------|-------|-----|---------|----------|
| db-micro | 1 | 1 GB | 20 GB | $0.017 |
| db-small | 2 | 4 GB | 100 GB | $0.068 |
| db-medium | 4 | 16 GB | 500 GB | $0.272 |
| db-large | 8 | 32 GB | 1 TB | $0.544 |
| db-xlarge | 16 | 64 GB | 2 TB | $1.088 |

## Creating a Database

### Via CLI
```bash
cloudnova db create \
  --name my-production-db \
  --engine postgresql \
  --version 16 \
  --class db-medium \
  --region us-east-1 \
  --multi-az true \
  --backup-retention 7 \
  --encryption true
```

### Via Web Console
1. Navigate to **Databases → Create Database**
2. Select engine and version
3. Choose instance class based on workload
4. Configure storage (auto-scaling recommended)
5. Enable Multi-AZ for production workloads
6. Set backup retention period
7. Configure network access (VPC, security groups)

## High Availability

### Multi-AZ Deployment
- Maintains a synchronous standby replica in a different availability zone
- Automatic failover in case of primary failure (typically < 60 seconds)
- No application changes required — DNS automatically points to the new primary
- Recommended for all production databases

### Read Replicas
- Asynchronous replication for read-heavy workloads
- Up to 5 read replicas per primary
- Can be in different regions for geographic distribution
- Replication lag typically < 1 second

```bash
# Create a read replica
cloudnova db create-replica \
  --source my-production-db \
  --name my-read-replica \
  --class db-small \
  --region eu-central-1
```

## Backup and Recovery

### Automated Backups
- Daily automated snapshots (configurable retention: 1-35 days)
- Point-in-Time Recovery (PITR) with 5-minute granularity
- Backups stored in CloudVault with cross-region replication

### Manual Snapshots
```bash
# Create a manual snapshot
cloudnova db snapshot create --database my-production-db --name pre-migration-backup

# List snapshots
cloudnova db snapshot list --database my-production-db

# Restore from snapshot
cloudnova db restore --snapshot snap-abc123 --name restored-db --class db-medium
```

### Point-in-Time Recovery
```bash
# Restore to a specific timestamp
cloudnova db restore-pitr \
  --database my-production-db \
  --target-time "2026-06-19T10:30:00Z" \
  --name restored-db
```

## Database Migration

### Using CloudNova Database Migration Service (DMS)
1. Create a migration task: **Databases → Migration → Create Task**
2. Configure source and target databases
3. Select migration type:
   - **Full Load**: One-time migration of all data
   - **CDC (Change Data Capture)**: Ongoing replication
   - **Full Load + CDC**: Initial migration followed by ongoing sync
4. Map schemas and tables
5. Start migration and monitor progress

### Pre-Migration Checklist
- [ ] Verify source and target engines are compatible
- [ ] Ensure sufficient storage on the target
- [ ] Configure network connectivity between source and target
- [ ] Test with a small dataset first
- [ ] Plan for application cutover (update connection strings)
- [ ] Schedule during low-traffic period

## Troubleshooting

### Connection Timeout
1. Verify security group allows inbound traffic on the database port (5432 for PostgreSQL, 3306 for MySQL)
2. Check that your application is in the same VPC or has VPC peering configured
3. Verify the database is in `available` state: `cloudnova db describe --name my-db`
4. Test connectivity: `cloudnova db test-connection --name my-db`
5. Check max_connections limit: Default is 100 for db-small, 500 for db-medium

### Slow Query Performance
1. Enable slow query logging: `cloudnova db parameter set --name my-db --key slow_query_log --value 1`
2. Review slow query log: **Databases → Logs → Slow Queries**
3. Analyze query plans with `EXPLAIN ANALYZE`
4. Create appropriate indexes
5. Consider upgrading to a larger instance class
6. Enable Performance Insights: **Databases → Performance → Enable**
