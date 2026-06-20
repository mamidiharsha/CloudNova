# CloudNova — Billing and Pricing Guide

## Pricing Overview

CloudNova uses a **pay-as-you-go** pricing model with optional reserved capacity discounts. All prices are in USD and billed monthly.

## Compute Pricing

| Instance Type | vCPUs | RAM | On-Demand ($/hr) | Reserved 1-Year ($/hr) | Reserved 3-Year ($/hr) |
|---------------|-------|-----|-------------------|------------------------|------------------------|
| cn-micro-1 | 1 | 1 GB | $0.012 | $0.008 | $0.006 |
| cn-standard-2 | 2 | 4 GB | $0.048 | $0.032 | $0.024 |
| cn-standard-4 | 4 | 8 GB | $0.096 | $0.064 | $0.048 |
| cn-performance-8 | 8 | 32 GB | $0.384 | $0.256 | $0.192 |
| cn-gpu-v100 | 8 | 64 GB | $2.48 | $1.65 | $1.24 |

## Storage Pricing

| Service | Price |
|---------|-------|
| Object Storage (CloudVault) | $0.023/GB/month |
| Block Storage (SSD) | $0.10/GB/month |
| Block Storage (HDD) | $0.045/GB/month |
| Snapshot Storage | $0.05/GB/month |
| Data Transfer (Outbound) | First 10 GB free, then $0.09/GB |

## Support Tiers

| Tier | Monthly Cost | Response Time | Features |
|------|-------------|---------------|----------|
| Basic | Free | 48 hours | Email support, documentation |
| Business | $100/month | 4 hours | Phone + email, technical advisor |
| Enterprise | $500/month | 15 minutes | 24/7 phone, dedicated TAM, SLA credits |

## Invoice and Payment

### Payment Methods
- Credit/debit cards (Visa, Mastercard, Amex)
- Wire transfer (Enterprise tier only, minimum $1,000)
- Purchase orders (Enterprise tier, requires approval)

### Billing Cycle
- Invoices are generated on the 1st of each month
- Payment is due within 15 days of invoice date
- Late payments incur a 1.5% monthly interest charge
- Accounts with payments overdue by 30+ days may be suspended

### Billing Alerts
Set up billing alerts at **Settings → Billing → Alerts**:
- Budget threshold alerts (50%, 75%, 90%, 100%)
- Anomaly detection for unusual spending spikes
- Weekly and monthly spending summaries via email

## Cost Optimization Tips
1. **Use reserved instances** for predictable workloads (save up to 50%)
2. **Enable auto-scaling** to avoid over-provisioning
3. **Delete unused resources**: Unattached volumes, old snapshots, idle instances
4. **Use lifecycle policies** to transition infrequently accessed data to cheaper storage
5. **Review the Cost Explorer** dashboard monthly at **Billing → Cost Explorer**

## Disputes and Adjustments
For billing disputes, contact our billing team at billing@cloudnova.io or call +1-800-CLOUDNOVA. Disputes must be filed within 60 days of the invoice date. Resolution typically takes 5-10 business days.
