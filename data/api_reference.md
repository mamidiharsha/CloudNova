# CloudNova — API Reference

## Base URL
```
https://api.cloudnova.io/v2
```

## Authentication

### API Key Authentication
Include your API key in the request header:
```
Authorization: Bearer cn_api_key_xxxxxxxxxxxxxxxxxxxx
```

### OAuth2 Token
For user-context operations, use OAuth2:
```bash
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "compute:read compute:write"
}
```

## Rate Limits

| Endpoint Category | Requests/Second | Burst |
|---|---|---|
| Read (GET, LIST) | 100 | 200 |
| Write (POST, PUT, DELETE) | 20 | 40 |
| Authentication | 10 | 20 |
| Bulk Operations | 5 | 10 |

Rate limit headers are included in every response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1719868500
```

## Compute API

### List Instances
```bash
GET /compute/instances?region=us-east-1&status=running&limit=20
```

### Create Instance
```bash
POST /compute/instances
{
  "name": "web-server-1",
  "instance_type": "cn-standard-2",
  "image_id": "img-ubuntu2204",
  "region": "us-east-1",
  "availability_zone": "us-east-1a",
  "key_name": "my-ssh-key",
  "security_groups": ["sg-web"],
  "tags": {"environment": "production"}
}
```

Response (201 Created):
```json
{
  "instance_id": "cn-i-abc123def456",
  "status": "pending",
  "public_ip": null,
  "private_ip": "10.0.1.15",
  "created_at": "2026-06-19T12:00:00Z"
}
```

### Terminate Instance
```bash
DELETE /compute/instances/cn-i-abc123def456
```

## Storage API

### Upload Object
```bash
PUT /vault/{bucket-name}/{object-key}
Content-Type: application/octet-stream
X-CloudNova-Storage-Class: STANDARD

<binary-data>
```

### Download Object
```bash
GET /vault/{bucket-name}/{object-key}
```

### Generate Pre-signed URL
```bash
POST /vault/{bucket-name}/{object-key}/presign
{
  "expiration_seconds": 3600,
  "method": "GET"
}
```

## SDK Support

### Python SDK
```bash
pip install cloudnova-sdk
```

```python
from cloudnova import CloudNovaClient

client = CloudNovaClient(api_key="cn_api_key_xxx")

# List instances
instances = client.compute.list_instances(region="us-east-1")

# Create instance
instance = client.compute.create_instance(
    name="my-app",
    instance_type="cn-standard-2",
    image_id="img-ubuntu2204"
)
print(f"Instance {instance.id} created: {instance.status}")
```

### JavaScript SDK
```bash
npm install @cloudnova/sdk
```

```javascript
const { CloudNova } = require('@cloudnova/sdk');
const client = new CloudNova({ apiKey: 'cn_api_key_xxx' });

const instances = await client.compute.listInstances({ region: 'us-east-1' });
```

## Webhooks

### Event Types
| Event | Description |
|-------|-------------|
| `instance.created` | New instance launched |
| `instance.terminated` | Instance permanently deleted |
| `instance.state_changed` | Instance state transition |
| `alarm.triggered` | Monitoring alarm triggered |
| `billing.threshold_reached` | Billing alert threshold met |

### Webhook Configuration
```bash
POST /webhooks
{
  "url": "https://your-app.com/webhooks/cloudnova",
  "events": ["instance.state_changed", "alarm.triggered"],
  "secret": "your_webhook_secret"
}
```

## Error Response Format
All API errors follow this structure:
```json
{
  "error": {
    "code": "InvalidParameter",
    "message": "The parameter 'instance_type' is not valid. Valid types: cn-standard-1, cn-standard-2, ...",
    "request_id": "req-abc123",
    "documentation_url": "https://docs.cloudnova.io/errors/InvalidParameter"
  }
}
```
