# CloudNova Platform — Getting Started Guide

## Welcome to CloudNova

CloudNova is an enterprise-grade cloud platform that provides compute, storage, networking, and managed database services. This guide will help you set up your account and deploy your first application.

## Account Setup

### Step 1: Create Your Account
1. Visit [https://console.cloudnova.io/signup](https://console.cloudnova.io/signup)
2. Enter your business email address
3. Choose your organization name
4. Select your primary region (US-East, US-West, EU-Central, AP-Southeast)
5. Verify your email address within 24 hours

### Step 2: Configure Multi-Factor Authentication (MFA)
MFA is **required** for all CloudNova accounts. Supported methods:
- **Authenticator App** (Google Authenticator, Authy) — Recommended
- **SMS Verification** — Available for Business and Enterprise tiers
- **Hardware Security Key** (YubiKey) — Available for Enterprise tier

### Step 3: Set Up Your First Project
1. Navigate to **Dashboard → Projects → Create New Project**
2. Assign a project name and select a billing account
3. Choose your default region and availability zone
4. Enable audit logging (recommended for production workloads)

## Quick Deploy: Your First Application

### Using the CloudNova CLI
```bash
# Install the CLI
pip install cloudnova-cli

# Authenticate
cloudnova auth login

# Create a compute instance
cloudnova compute create --name my-app --type cn-standard-2 --region us-east-1

# Deploy your application
cloudnova deploy --source ./my-app --target my-app-instance
```

### Using the Web Console
1. Go to **Compute → Instances → Launch Instance**
2. Select instance type: `cn-standard-2` (2 vCPUs, 4 GB RAM)
3. Choose an operating system image (Ubuntu 22.04 LTS recommended)
4. Configure networking (default VPC is created automatically)
5. Add SSH key for secure access
6. Click **Launch**

## Support Resources
- **Documentation**: https://docs.cloudnova.io
- **Community Forum**: https://community.cloudnova.io
- **Support Portal**: https://support.cloudnova.io
- **Status Page**: https://status.cloudnova.io

## Common First-Time Issues
- **Email verification not received**: Check spam/junk folders. Resend from the login page.
- **MFA setup failure**: Ensure your device clock is synchronized (NTP).
- **CLI authentication error**: Run `cloudnova auth logout` then `cloudnova auth login` again.
