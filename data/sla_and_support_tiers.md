# CloudNova — SLA and Support Tiers

## Service Level Agreement (SLA)

### Uptime Guarantees

| Service | Monthly Uptime SLA | Credit for Breach |
|---------|-------------------|-------------------|
| Compute Instances | 99.99% | See credit table below |
| CloudVault (Object Storage) | 99.99% | See credit table below |
| BlockStore (Block Storage) | 99.99% | See credit table below |
| Managed Databases | 99.95% | See credit table below |
| Load Balancers | 99.99% | See credit table below |
| DNS Service | 100% | See credit table below |

### SLA Credit Schedule

| Monthly Uptime Percentage | Service Credit |
|---------------------------|---------------|
| 99.0% - 99.99% | 10% of monthly bill |
| 95.0% - 99.0% | 25% of monthly bill |
| Below 95.0% | 50% of monthly bill |

### Claiming SLA Credits
1. Submit a claim within 30 days of the incident
2. Go to **Support → SLA Claims → New Claim**
3. Provide the affected resource IDs and time window
4. CloudNova will verify against internal monitoring data
5. Approved credits are applied to the next billing cycle
6. Credits do not roll over and cannot be converted to cash

### Exclusions
SLA does not apply to:
- Scheduled maintenance windows (notified 72 hours in advance)
- Force majeure events
- Customer-caused outages (misconfiguration, exceeding quotas)
- Beta or preview services
- Free tier accounts

## Support Tiers

### Basic Support (Free)
- **Included with**: All accounts
- **Response Time**: 48 business hours
- **Channels**: Email only
- **Coverage**: Billing inquiries, account issues
- **Documentation**: Full access to online documentation and community forums
- **Support Hours**: Monday–Friday, 9 AM – 6 PM (customer's timezone)

### Business Support ($100/month)
- **Response Time**: 
  - Critical: 1 hour
  - High: 4 hours
  - Normal: 12 hours
  - Low: 24 hours
- **Channels**: Email + Phone
- **Coverage**: Technical support, architecture guidance, performance optimization
- **Extras**: 
  - Monthly health check report
  - 1 architecture review per quarter
  - Access to premium knowledge base articles
- **Support Hours**: 24/5 (Monday–Friday)

### Enterprise Support ($500/month)
- **Response Time**:
  - Critical: 15 minutes
  - High: 1 hour
  - Normal: 4 hours
  - Low: 12 hours
- **Channels**: Email + Phone + Slack + Dedicated Portal
- **Coverage**: Full technical support, proactive monitoring, dedicated TAM
- **Extras**:
  - Dedicated Technical Account Manager (TAM)
  - Quarterly business reviews
  - Infrastructure event management
  - Well-Architected reviews
  - Training credits ($1,000/year)
  - Early access to new features
- **Support Hours**: 24/7/365

## Incident Severity Levels

| Severity | Definition | Example |
|----------|------------|---------|
| **Critical** | Production system down, no workaround | Complete service outage |
| **High** | Production system impaired, workaround available | Degraded performance |
| **Normal** | Non-production issue or feature question | Development environment issue |
| **Low** | General question or feature request | Documentation clarification |

## Maintenance Windows

### Scheduled Maintenance
- Notification: 72 hours in advance via email and status page
- Preferred window: Sunday 02:00 - 06:00 UTC
- Enterprise customers can request custom maintenance windows
- Most maintenance is performed with zero downtime using rolling updates

### Emergency Maintenance
- Performed only for critical security patches or imminent hardware failures
- Best-effort notification (minimum 1 hour)
- Applied as quickly as possible regardless of maintenance window
