# CloudNova — Account Management Guide

## User Roles and Permissions

CloudNova uses Role-Based Access Control (RBAC) with the following predefined roles:

### Organization Roles
| Role | Description | Permissions |
|------|-------------|-------------|
| **Owner** | Full organization control | All permissions, billing management, delete org |
| **Admin** | Organization administration | Manage users, projects, settings (cannot delete org) |
| **Member** | Standard user access | Access assigned projects, create resources |
| **Viewer** | Read-only access | View resources and dashboards only |

### Project Roles
| Role | Description |
|------|-------------|
| **Project Admin** | Full control within a project |
| **Developer** | Create, modify, and delete resources |
| **Operator** | Monitor and manage running resources |
| **Read-Only** | View resources and logs |

### Managing Users
1. Navigate to **Settings → Organization → Members**
2. Click **Invite Member**
3. Enter email address and select role
4. User receives invitation valid for 7 days

## Single Sign-On (SSO)

### Supported Identity Providers
- **SAML 2.0**: Okta, Azure AD, OneLogin, PingFederate
- **OpenID Connect (OIDC)**: Google Workspace, Auth0

### SSO Configuration
1. Go to **Settings → Security → SSO**
2. Upload your IdP metadata XML or enter the SSO URL
3. Map IdP attributes to CloudNova roles
4. Enable SSO enforcement (optional — disables password login)
5. Test with a non-admin account before enforcing

## Multi-Factor Authentication (MFA)

### Enabling MFA
1. Go to **Profile → Security → MFA**
2. Select your preferred method
3. Follow the setup wizard
4. Save your backup recovery codes in a secure location

### MFA Recovery
If you lose access to your MFA device:
1. Use one of your **backup recovery codes** to log in
2. If no recovery codes are available, contact support with government-issued ID verification
3. Account recovery takes 24-72 hours for security verification
4. A temporary bypass code will be sent to your verified email

## Account Recovery

### Password Reset
1. Click **"Forgot Password"** on the login page
2. Enter your registered email address
3. Check your email for the reset link (valid for 1 hour)
4. Create a new password meeting the requirements:
   - Minimum 12 characters
   - At least one uppercase, lowercase, number, and special character
   - Cannot reuse the last 5 passwords

### Account Lockout
- After **5 failed login attempts**, the account is locked for 30 minutes
- After **10 failed attempts**, the account is locked until manual unlock by an admin
- Locked accounts can be unlocked at **Settings → Members → Unlock Account**

### Account Deletion
To permanently delete your CloudNova account:
1. Download all your data via **Settings → Data Export**
2. Cancel all active subscriptions
3. Settle any outstanding balance
4. Go to **Settings → Organization → Delete Organization**
5. Confirm with your password and MFA code
6. Account is scheduled for deletion in 30 days (can be cancelled during this period)

## API Key Management
- Generate API keys at **Profile → API Keys → Generate New Key**
- Each key can have scoped permissions (read-only, read-write, admin)
- Keys can be set to expire after a defined period
- Rotate keys regularly (recommended: every 90 days)
- Revoke compromised keys immediately at **Profile → API Keys → Revoke**
