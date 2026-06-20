# CloudNova — Security Best Practices

## Overview

Security is a shared responsibility between CloudNova and its customers. CloudNova secures the infrastructure; customers secure their data, configurations, and access controls.

## Identity and Access Management (IAM)

### Principle of Least Privilege
- Grant only the minimum permissions required for each role
- Use project-level roles instead of organization-level when possible
- Review and audit permissions quarterly
- Remove access for departing team members within 24 hours

### IAM Policy Example
```json
{
  "version": "2024-01-01",
  "statements": [
    {
      "effect": "allow",
      "actions": ["compute:Describe*", "compute:List*"],
      "resources": ["projects/my-project/*"]
    },
    {
      "effect": "deny",
      "actions": ["compute:Terminate*"],
      "resources": ["*"]
    }
  ]
}
```

### Service Accounts
- Use service accounts for automated processes (CI/CD, monitoring)
- Never use personal credentials in automation scripts
- Rotate service account keys every 90 days
- Limit service account scope to specific projects

## Encryption

### Encryption at Rest
- All CloudVault objects are encrypted with AES-256 by default
- BlockStore volumes support encryption with CloudNova-managed keys or customer-managed keys (CMK)
- Database services encrypt data at rest automatically

### Encryption in Transit
- All CloudNova API communications use TLS 1.3
- Internal service-to-service communication is encrypted by default
- Load balancers support TLS termination with custom certificates
- Enforce HTTPS-only with redirect rules on Application Load Balancers

### Customer-Managed Keys (CMK)
1. Create a key at **Security → Key Management → Create Key**
2. Define key rotation policy (automatic rotation every 365 days recommended)
3. Assign key to resources during creation
4. Audit key usage via **Security → Key Management → Audit Log**

## Audit Logging

### CloudTrail
- Records all API calls across your CloudNova account
- Enabled by default for management events
- Configure data event logging for sensitive resources
- Logs stored in CloudVault with 90-day default retention

### Log Analysis
```bash
# View recent API activity
cloudnova audit list --since 24h

# Filter by specific action
cloudnova audit list --action compute:TerminateInstance --since 7d

# Export logs for analysis
cloudnova audit export --since 30d --format json --output audit-logs.json
```

## Network Security

### Best Practices
1. **Use private subnets** for databases and internal services
2. **Enable VPC Flow Logs** to monitor network traffic patterns
3. **Implement Web Application Firewall (WAF)** for public-facing applications
4. **Use NAT Gateways** instead of assigning public IPs to private instances
5. **Regularly review security group rules** — remove unused rules

### DDoS Protection
- CloudNova Shield (Basic) is enabled for all accounts at no cost
- CloudNova Shield (Advanced) provides enhanced protection for $3,000/month
- Advanced features: real-time attack visibility, 24/7 DDoS response team, cost protection

## Compliance

CloudNova maintains the following certifications:
- SOC 2 Type II
- ISO 27001
- HIPAA (available for Enterprise tier)
- GDPR compliant
- PCI DSS Level 1

### Compliance Reports
Access compliance reports at **Security → Compliance → Reports**. Available reports include SOC 2 audit report, penetration test summary, and data processing agreements.

## Incident Response

If you suspect a security breach:
1. **Immediately rotate** all potentially compromised credentials
2. **Enable enhanced logging** on affected resources
3. **Contact CloudNova Security** at security@cloudnova.io or call the 24/7 hotline
4. **Preserve evidence** — do not terminate affected instances
5. **Review audit logs** for unauthorized access patterns
