# CloudNova — Troubleshooting Common Errors

## Error Code Reference

### Authentication Errors (4xx)

#### Error 401: Unauthorized
**Message**: `Authentication failed: Invalid or expired credentials`

**Causes**:
- API key has been revoked or expired
- JWT token has expired (tokens are valid for 1 hour)
- Incorrect API key used for the environment (staging vs production)

**Resolution**:
1. Check API key validity: **Profile → API Keys**
2. Regenerate the token: `cloudnova auth token refresh`
3. Verify the API endpoint matches your environment
4. Ensure the system clock is synchronized (JWT validation is time-sensitive)

#### Error 403: Forbidden
**Message**: `Access denied: Insufficient permissions for this action`

**Causes**:
- User role does not have the required permission
- Resource belongs to a different project
- Organization policy restricts the action

**Resolution**:
1. Check your current role: `cloudnova iam whoami`
2. Request permission from your project admin
3. Verify the resource exists in your current project context
4. Review organization policies: **Settings → Organization → Policies**

### Resource Errors (4xx)

#### Error 404: Resource Not Found
**Message**: `Resource not found: <resource-id> does not exist`

**Causes**:
- Resource has been terminated/deleted
- Incorrect resource ID or name
- Resource is in a different region

**Resolution**:
1. Verify the resource ID: `cloudnova resource describe <resource-id>`
2. Check all regions: `cloudnova resource find --name <name> --all-regions`
3. Check the recycle bin: **Resources → Recycle Bin** (retained for 30 days)

#### Error 409: Conflict
**Message**: `Resource conflict: The resource is in a conflicting state`

**Causes**:
- Attempting to modify a resource that is being updated
- Naming conflict with an existing resource
- Concurrent operations on the same resource

**Resolution**:
1. Wait 30 seconds and retry the operation
2. Check the resource state: `cloudnova resource describe <resource-id>`
3. Use unique naming conventions to avoid conflicts

### Server Errors (5xx)

#### Error 500: Internal Server Error
**Message**: `Internal error: An unexpected error occurred`

**Resolution**:
1. Retry the request after 60 seconds
2. Check CloudNova status page: https://status.cloudnova.io
3. If persistent, contact support with the request ID from the response headers

#### Error 502: Bad Gateway
**Message**: `Bad gateway: The upstream service is unavailable`

**Causes**:
- Target service is down or overloaded
- Load balancer cannot reach backend instances
- Network configuration issue

**Resolution**:
1. Check target instance health
2. Verify security group allows traffic from the load balancer
3. Review application logs for startup failures
4. Increase health check timeout if the application is slow to start

#### Error 503: Service Unavailable
**Message**: `Service unavailable: The service is temporarily overloaded`

**Resolution**:
1. Implement exponential backoff in your retry logic
2. Check current service quotas: **Settings → Quotas**
3. Scale up resources if approaching limits
4. Contact support if the issue persists beyond 30 minutes

#### Error 429: Rate Limit Exceeded
**Message**: `Rate limit exceeded: Too many requests`

**Rate Limits**:
| API Category | Limit |
|---|---|
| Read operations | 100 requests/second |
| Write operations | 20 requests/second |
| Authentication | 10 requests/second |

**Resolution**:
1. Implement exponential backoff with jitter
2. Use batch API endpoints where available
3. Cache read responses locally
4. Request a rate limit increase: **Settings → Quotas → Request Increase**

## Connectivity Issues

### SSH Connection Refused
1. Verify the instance is in `running` state
2. Check security group allows port 22 from your IP
3. Verify your SSH key matches: `cloudnova compute describe-key --instance-id <ID>`
4. Check if the instance's SSH daemon is running (use CloudNova console)
5. Try connecting via the web-based console: **Compute → Instances → Console**

### Application Not Responding
1. Check instance health: **Monitoring → Instance Metrics**
2. Verify the application process is running: `cloudnova compute run-command --instance-id <ID> --command "systemctl status myapp"`
3. Check application logs: `cloudnova logs search --group /app/production --query "ERROR"`
4. Verify load balancer target group health
5. Check for resource exhaustion (disk space, memory, file descriptors)

## Data Recovery

### Accidental Deletion
1. **Instances**: Check **Resources → Recycle Bin** (30-day retention)
2. **Storage**: Use CloudVault versioning to restore previous versions
3. **Databases**: Restore from automated snapshot: **Database → Snapshots → Restore**
4. **Configuration**: Check CloudTrail for the delete event details

### Restoring from Snapshot
```bash
# List available snapshots
cloudnova snapshot list --resource-type blockstore

# Restore a volume from snapshot
cloudnova blockstore create --from-snapshot snap-abc123 --name restored-volume --az us-east-1a

# Attach to instance
cloudnova blockstore attach --volume-id vol-xyz789 --instance-id cn-i-abc123 --device /dev/sdf
```
