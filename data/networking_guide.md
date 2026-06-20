# CloudNova — Networking Guide

## Virtual Private Cloud (VPC)

### Overview
A VPC is an isolated virtual network within CloudNova. Each project gets a default VPC, and you can create up to 5 VPCs per region.

### Default VPC Configuration
- CIDR Block: `10.0.0.0/16` (65,536 IP addresses)
- Default subnets in each availability zone
- Internet Gateway attached automatically
- Default security group (allows all outbound, denies all inbound)

### Creating a Custom VPC
```bash
# Create VPC
cloudnova network vpc create --name production-vpc --cidr 172.16.0.0/16

# Create subnets
cloudnova network subnet create --vpc production-vpc --name public-subnet --cidr 172.16.1.0/24 --az us-east-1a
cloudnova network subnet create --vpc production-vpc --name private-subnet --cidr 172.16.2.0/24 --az us-east-1b

# Create and attach internet gateway
cloudnova network igw create --name prod-igw --vpc production-vpc
```

## Load Balancers

### Types
| Type | Layer | Use Case |
|------|-------|----------|
| Application LB (ALB) | Layer 7 (HTTP/HTTPS) | Web applications, microservices |
| Network LB (NLB) | Layer 4 (TCP/UDP) | High-performance, low-latency |
| Gateway LB (GLB) | Layer 3 | Third-party appliances |

### ALB Configuration
1. Go to **Networking → Load Balancers → Create**
2. Select **Application Load Balancer**
3. Configure listeners (HTTP:80, HTTPS:443)
4. Upload SSL certificate or use CloudNova Certificate Manager
5. Define target groups and health checks
6. Set routing rules (path-based or host-based)

### Health Check Configuration
- **Path**: `/health` or `/api/status`
- **Interval**: 30 seconds (recommended)
- **Timeout**: 5 seconds
- **Healthy threshold**: 3 consecutive checks
- **Unhealthy threshold**: 2 consecutive failures

## DNS (CloudNova DNS)

### Features
- Managed DNS with global anycast network
- Automatic health checking and failover
- Support for A, AAAA, CNAME, MX, TXT, SRV records
- Latency-based routing for multi-region deployments

### Common DNS Operations
```bash
# Create a hosted zone
cloudnova dns create-zone --domain myapp.com

# Add an A record
cloudnova dns add-record --zone myapp.com --type A --name www --value 203.0.113.50 --ttl 300

# Add a CNAME for the load balancer
cloudnova dns add-record --zone myapp.com --type CNAME --name api --value my-alb.cloudnova.io --ttl 300
```

## Firewall Rules (Security Groups)

### Default Rules
- **Inbound**: Deny all (must explicitly allow)
- **Outbound**: Allow all

### Common Configurations
```bash
# Allow SSH from specific IP
cloudnova network sg add-rule --group web-sg --direction inbound --protocol tcp --port 22 --source 198.51.100.0/24

# Allow HTTP/HTTPS from anywhere
cloudnova network sg add-rule --group web-sg --direction inbound --protocol tcp --port 80 --source 0.0.0.0/0
cloudnova network sg add-rule --group web-sg --direction inbound --protocol tcp --port 443 --source 0.0.0.0/0

# Allow database access from app subnet only
cloudnova network sg add-rule --group db-sg --direction inbound --protocol tcp --port 5432 --source 172.16.1.0/24
```

## Troubleshooting

### Cannot Connect to Instance
1. Verify Security Group allows inbound traffic on the required port
2. Check that the instance has a public IP or is behind a NAT gateway
3. Verify route tables: **Networking → VPC → Route Tables**
4. Test with: `cloudnova network diagnose --instance-id <ID> --port <PORT>`
5. Check Network ACLs (stateless, applied at subnet level)

### Load Balancer 502 Errors
1. Verify target instances are healthy: **LB → Target Groups → Health Status**
2. Check that the target group port matches the application port
3. Increase health check grace period for slow-starting applications
4. Review application logs for startup errors
5. Verify security groups allow traffic from the load balancer
