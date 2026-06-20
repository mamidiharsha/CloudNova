# CloudNova — Deployment Pipeline Guide

## Overview

CloudNova Deployments provides a fully managed CI/CD service for automated application deployment. It supports blue-green deployments, canary releases, and automatic rollbacks.

## Deployment Strategies

### Rolling Deployment
- Gradually replaces instances with new versions
- Zero downtime during deployment
- Default strategy for most applications
- Configurable batch size and wait time between batches

### Blue-Green Deployment
- Maintains two identical environments (Blue = current, Green = new)
- Traffic switches instantly after Green is verified
- Easy rollback by switching back to Blue
- Higher cost (runs two environments during deployment)

### Canary Deployment
- Routes a small percentage of traffic to the new version
- Gradually increases traffic if metrics are healthy
- Automatic rollback if error rate exceeds threshold
- Best for high-risk changes

## Setting Up a Deployment Pipeline

### Step 1: Create a Pipeline
```yaml
# cloudnova-deploy.yaml
pipeline:
  name: my-app-pipeline
  trigger:
    branch: main
    events: [push, tag]
  
  stages:
    - name: build
      steps:
        - run: pip install -r requirements.txt
        - run: python -m pytest tests/
        - run: cloudnova build --source . --output build/

    - name: deploy-staging
      environment: staging
      strategy: rolling
      steps:
        - run: cloudnova deploy --target staging --source build/
        - run: cloudnova test --suite smoke --target staging

    - name: deploy-production
      environment: production
      strategy: blue-green
      approval: required
      steps:
        - run: cloudnova deploy --target production --source build/
        - run: cloudnova test --suite smoke --target production
        - run: cloudnova traffic switch --target production --to green
```

### Step 2: Configure Environments
```bash
# Create staging environment
cloudnova env create staging --region us-east-1 --instance-type cn-standard-2 --count 2

# Create production environment
cloudnova env create production --region us-east-1 --instance-type cn-standard-4 --count 4
```

### Step 3: Enable Auto-Rollback
```bash
cloudnova deploy config --environment production \
  --auto-rollback true \
  --rollback-trigger error-rate \
  --rollback-threshold 5 \
  --monitoring-period 300
```

## Rollback Procedures

### Automatic Rollback
Triggered when:
- Error rate exceeds the configured threshold (default: 5%)
- Health check failures exceed tolerance (default: 3 consecutive)
- Deployment timeout is reached (default: 30 minutes)

### Manual Rollback
```bash
# List recent deployments
cloudnova deploy list --environment production --limit 5

# Rollback to a specific version
cloudnova deploy rollback --environment production --to-version v2.3.1

# Rollback to the previous version
cloudnova deploy rollback --environment production --previous
```

## Environment Variables and Secrets

### Setting Variables
```bash
# Set a plain text variable
cloudnova env var set --environment production --key DATABASE_URL --value "postgresql://..."

# Set a secret (encrypted at rest)
cloudnova env secret set --environment production --key API_SECRET --value "sk-xxx..."

# List all variables
cloudnova env var list --environment production
```

### Secret Management
- Secrets are encrypted with AES-256 and stored in CloudNova Vault
- Secrets are injected as environment variables at runtime
- Secret values are never displayed in logs or the web console
- Rotate secrets without redeployment: `cloudnova env secret rotate`

## Monitoring Deployments

### Deployment Dashboard
View real-time deployment status at **Deployments → Dashboard**:
- Current deployment stage and progress
- Instance health status
- Error rate and latency metrics
- Deployment history and comparison

### Deployment Notifications
Configure notifications at **Deployments → Settings → Notifications**:
- Slack: Deployment start, success, failure, rollback
- Email: Deployment summary and error reports
- Webhook: Custom integrations

## Troubleshooting Deployments

### Deployment Stuck in "In Progress"
1. Check the deployment logs: `cloudnova deploy logs --deployment-id dep-xxx`
2. Verify instance health: `cloudnova deploy status --deployment-id dep-xxx`
3. Check for resource quota limits
4. Cancel and retry: `cloudnova deploy cancel --deployment-id dep-xxx`

### Application Not Starting After Deploy
1. Check application logs: `cloudnova logs search --group /app/production --query "ERROR" --since 30m`
2. Verify environment variables are set correctly
3. Check the application health check endpoint
4. Roll back to the previous version if needed
5. Review build artifacts for missing dependencies
