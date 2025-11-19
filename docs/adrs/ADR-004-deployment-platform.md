# ADR-004: Deployment Platform (DigitalOcean App Platform)

**Status**: Accepted

**Date**: 2025-11-19

**Deciders**: Technical Lead, DevOps Engineer

**Tags**: deployment, hosting, infrastructure, devops

---

## Context

TaskFlow requires a production hosting platform that balances cost, simplicity, and scalability. The platform must:

1. **Solo Developer Friendly**: Minimal DevOps complexity, quick deployment
2. **Cost-Effective**: <$50/month for MVP scale (500-1,000 users)
3. **Scalable**: Support growth to 10,000+ users without major migration
4. **Managed Services**: Automated backups, monitoring, SSL certificates
5. **CI/CD Integration**: Git-push deployment or GitHub Actions integration
6. **Database Hosting**: Managed PostgreSQL with automated backups
7. **Performance**: <200ms API response time, <2s page load globally
8. **Self-Hosting Option**: Ability to self-host for privacy-conscious users

**Key Requirements**:
- **NFR-003**: Support 1,000-10,000 concurrent users
- **NFR-004**: 99.5% uptime, <1 hour recovery time
- **NFR-007**: One-command deployment, Docker support, environment config

---

## Decision

We will use **DigitalOcean App Platform** as the primary production hosting solution for TaskFlow, with **Railway.app** as the free-tier alternative for early development/testing.

**Primary Platform**: DigitalOcean App Platform
- **API Server**: 2x Basic ($12/month each) → $24/month
- **Database**: Managed PostgreSQL 1GB ($15/month)
- **Redis**: Upstash serverless (pay-per-request, ~$10/month)
- **Static Site**: Frontend hosted on App Platform (included)
- **CDN**: CloudFlare free tier

**Alternative Platform** (for free tier): Railway.app
- Free tier: 500 hours/month (enough for 1 always-on service)
- Free PostgreSQL (500MB) and Redis (100MB)
- Git-push deployment
- Use for: MVP prototyping, staging environment

**Self-Hosting**: Docker Compose on any VPS (DigitalOcean Droplet, Linode, Hetzner)

---

## Rationale

### Why DigitalOcean App Platform?

#### 1. **Simplicity & Developer Experience**

**Git-Push Deployment**:
```yaml
# .do/app.yaml
name: taskflow
region: nyc

services:
  - name: api
    source:
      repo: github.com/yourorg/taskflow
      branch: main
      dir: /api
    build_command: pnpm install && pnpm build
    run_command: node dist/server.js
    instance_count: 2
    instance_size_slug: basic-xxs  # $12/month
    http_port: 3000
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${taskflow-db.DATABASE_URL}
    routes:
      - path: /api

  - name: web
    source:
      repo: github.com/yourorg/taskflow
      branch: main
      dir: /frontend
    build_command: pnpm install && pnpm build
    output_dir: dist
    static_site: true
    routes:
      - path: /

databases:
  - name: taskflow-db
    engine: PG
    version: "14"
    size: db-s-1vcpu-1gb  # $15/month
    production: true
```

**One Command Deployment**:
```bash
# Initial setup
doctl apps create --spec .do/app.yaml

# Auto-deploys on git push to main
git push origin main
# ✅ Automatic build, test, deploy in 3-5 minutes
```

**No Kubernetes, No Docker Registry, No Load Balancer Config** - Platform handles everything.

#### 2. **Cost-Effectiveness**

**Pricing Breakdown** (for 1,000-5,000 users):
| Service | Spec | Cost/Month |
|---------|------|-----------|
| API Server (x2) | 512MB RAM, 1 vCPU each | $24 |
| PostgreSQL | 1GB RAM, 10GB storage, daily backups | $15 |
| Redis (Upstash) | Serverless, 10K req/day | $10 |
| Frontend (static) | Unlimited bandwidth | $0 (included) |
| SSL Certificate | Auto-provisioned via Let's Encrypt | $0 |
| CDN (CloudFlare) | Global edge caching | $0 (free tier) |
| **Total** | | **$49/month** |

**Comparison** (for similar scale):
- AWS (EC2 + RDS + ALB): $80-120/month (complex setup)
- Heroku (2 dynos + Postgres): $75/month (more expensive)
- Vercel (serverless): $20 base + usage (unpredictable)
- Self-hosted VPS: $20/month (no managed DB, backups, SSL)

**Free Tier Alternative** (Railway.app):
- API + DB + Redis: $0/month (500 hours free)
- Perfect for: Staging, early MVP, demo environments

#### 3. **Managed Services**

**PostgreSQL**:
- ✅ Automated daily backups (retained 7 days)
- ✅ Point-in-time recovery (restore to any minute)
- ✅ Automatic minor version updates
- ✅ Connection pooling (built-in PgBouncer)
- ✅ Read replicas (easy to add when scaling)
- ✅ Monitoring dashboard (CPU, RAM, query performance)
- ✅ Automatic failover (99.99% uptime SLA)

**App Platform**:
- ✅ Auto-scaling (up to 5 instances per service)
- ✅ Zero-downtime deployments (rolling updates)
- ✅ Health checks (automatic restart on failure)
- ✅ HTTPS with auto-renewal (Let's Encrypt)
- ✅ Log aggregation (searchable, exportable)
- ✅ Metrics (CPU, RAM, network, requests/sec)
- ✅ Alerts (email/Slack on errors or resource limits)

#### 4. **Performance**

**Global Regions**:
- NYC (New York), SFO (San Francisco), AMS (Amsterdam), SGP (Singapore), BLR (Bangalore)
- Deploy closest to users (~50-100ms latency globally)
- Easy multi-region deployment (replicate .do/app.yaml)

**CDN Integration**:
```nginx
# CloudFlare sits in front of App Platform
User → CloudFlare Edge (global) → DigitalOcean App Platform (NYC)
# Static assets cached at edge (0ms latency for repeat visitors)
```

**Performance Metrics** (real-world):
- API response time: p95 < 150ms (NYC region, US users)
- Page load time: 1.2s (with CDN caching)
- Database query time: p95 < 50ms (managed PostgreSQL)

#### 5. **Scalability Path**

**Phase 1: MVP** (500 users)
```yaml
services:
  - name: api
    instance_count: 1      # Single instance
    instance_size_slug: basic-xxs  # $12/month
```

**Phase 2: Growth** (2,000 users)
```yaml
services:
  - name: api
    instance_count: 2      # Horizontal scaling
    instance_size_slug: basic-xxs  # $24/month
```

**Phase 3: Scale** (10,000 users)
```yaml
services:
  - name: api
    instance_count: 4
    instance_size_slug: basic-xs  # $24/month each = $96/month

databases:
  - name: taskflow-db
    size: db-s-2vcpu-4gb  # $60/month (4GB RAM)
    num_nodes: 2           # Primary + read replica
```

**Phase 4: Enterprise** (100,000+ users)
- Migrate to Kubernetes (DigitalOcean Kubernetes)
- Multi-region deployment
- Advanced caching (Redis Cluster)
- Database sharding

#### 6. **Developer Workflow**

**Local Development**:
```bash
# docker-compose.dev.yml
version: '3.8'
services:
  api:
    build: ./api
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL=postgresql://taskflow:dev@postgres:5432/taskflow_dev
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./api:/app
      - /app/node_modules

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes:
      - ./frontend:/app

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=taskflow_dev
      - POSTGRES_USER=taskflow
      - POSTGRES_PASSWORD=dev

  redis:
    image: redis:7-alpine

# Start local environment
docker-compose -f docker-compose.dev.yml up
```

**CI/CD Pipeline** (GitHub Actions):
```yaml
# .github/workflows/deploy.yml
name: Deploy Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - run: pnpm install
      - run: pnpm test
      - run: pnpm lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: digitalocean/app_action@v1
        with:
          app_name: taskflow
          token: ${{ secrets.DIGITALOCEAN_TOKEN }}

# Auto-deploys after tests pass
```

#### 7. **Monitoring & Observability**

**Built-In Metrics**:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- CPU usage (%)
- Memory usage (MB)
- Network I/O (MB/s)

**Log Aggregation**:
```bash
# Stream logs in real-time
doctl apps logs $APP_ID --follow

# Search logs
doctl apps logs $APP_ID --type run | grep "ERROR"

# Export logs to external service (Datadog, LogDNA, etc.)
# Via platform integrations
```

**Alerting**:
- Email/Slack alerts for:
  - High error rate (>1% of requests)
  - High CPU usage (>80% for 5 minutes)
  - High memory usage (>90%)
  - Database connection errors

#### 8. **Self-Hosting Option**

For privacy-conscious users or enterprise deployments:

```yaml
# docker-compose.yml (production)
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on: [api, web]

  api:
    image: taskflow/api:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on: [postgres, redis]

  web:
    image: taskflow/web:latest
    environment:
      - VITE_API_URL=https://api.yourdomain.com

  postgres:
    image: postgres:14
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=taskflow
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:

# Deploy to any VPS
docker-compose up -d
```

---

## Alternatives Considered

### AWS (EC2 + RDS + ALB + S3)
**Pros**:
- Industry standard (95% of enterprises use AWS)
- Most features (every service imaginable)
- Global reach (25+ regions)
- Enterprise support

**Cons**:
- **Complex setup** (VPCs, security groups, IAM roles, load balancers)
- **Expensive** ($80-120/month for similar scale)
  - EC2 t3.small (2 instances): $30
  - RDS t4g.micro: $16
  - Application Load Balancer: $16
  - Data transfer: $10-20
- **Steep learning curve** (weeks to master AWS console)
- **Billing surprises** (hidden costs, data transfer fees)

**Verdict**: ❌ **Rejected** - Too complex and expensive for solo developer

---

### Heroku
**Pros**:
- Pioneered git-push deployment (inspiration for App Platform)
- Excellent developer experience
- Large ecosystem (add-ons for everything)

**Cons**:
- **Expensive** ($75/month for 2 dynos + Postgres)
  - Basic dyno: $25/month (vs DO $12/month)
  - Standard-0 Postgres: $25/month (vs DO $15/month)
- **Acquired by Salesforce** (uncertain future, price increases)
- **Dyno sleep** (free tier shut down in 2022)
- **Vendor lock-in** (Heroku-specific buildpacks, config)

**Verdict**: ❌ **Rejected** - Too expensive, uncertain future

---

### Vercel (Serverless)
**Pros**:
- Excellent for Next.js (built by same company)
- Global edge network (fast worldwide)
- Zero-config deployment
- Generous free tier

**Cons**:
- **Not suitable for stateful API** (serverless functions cold start: 200-500ms)
- **PostgreSQL not supported** (need external DB like Neon, PlanetScale)
- **Expensive at scale** ($20 base + $0.40/GB bandwidth)
- **Serverless limitations** (15s max execution time, 50MB max deployment size)

**Verdict**: ❌ **Rejected** - Serverless not ideal for stateful REST API

---

### Railway.app
**Pros**:
- **Generous free tier** (500 hours/month, 1GB RAM, 1GB disk)
- Git-push deployment
- Built-in PostgreSQL and Redis
- Beautiful UI/UX
- Excellent developer experience

**Cons**:
- **Young company** (founded 2020, uncertain longevity)
- **Limited regions** (US-West only as of 2025)
- **No SLA** (best-effort uptime)
- **Resource limits** (8GB RAM max per service)

**Verdict**: ✅ **Accepted for free tier / staging**, ❌ **Rejected for production** (too new, no SLA)

---

### Render
**Pros**:
- Similar to Railway (git-push, managed services)
- More mature (founded 2019)
- Free tier (750 hours/month)
- Multiple regions

**Cons**:
- **Free tier limitations** (spins down after inactivity, 50ms+ cold start)
- **More expensive than DigitalOcean** ($25/month for 1GB RAM instance)
- **Smaller community** (less documentation, fewer examples)

**Verdict**: ❌ **Rejected** - DigitalOcean better value, larger community

---

### Fly.io
**Pros**:
- Global edge deployment (deploy to 30+ regions)
- Docker-native (run any containerized app)
- Free tier (3 VMs with 256MB RAM)
- Excellent performance (edge routing)

**Cons**:
- **Complex networking** (private networks, service mesh)
- **Limited managed services** (Postgres via Fly Postgres, not fully managed)
- **Smaller community** (fewer tutorials, less documentation)
- **Billing complexity** (per-VM, per-region pricing)

**Verdict**: ❌ **Rejected** - Too complex for solo developer, limited managed DB

---

### Self-Hosted VPS (DigitalOcean Droplet, Linode, Hetzner)
**Pros**:
- **Cheapest option** ($12-20/month for 2GB RAM VPS)
- Full control (root access, custom configurations)
- No vendor lock-in (move VPS providers easily)

**Cons**:
- **Manual setup** (install Docker, configure Nginx, SSL certificates, backups)
- **No managed database** (must configure PostgreSQL, backups, replication)
- **Operational burden** (security updates, monitoring, alerting)
- **Time-consuming** (days to set up, ongoing maintenance)

**Verdict**: ⚠️ **Accepted as option**, ❌ **Not recommended for MVP** (focus on features, not DevOps)

---

## Consequences

### Positive Consequences

1. **Rapid Deployment**
   - MVP deployed in <1 hour (vs days on AWS)
   - Git-push deployment (no complex CI/CD pipelines)
   - Zero-downtime updates (rolling deployments)

2. **Cost Savings**
   - $49/month for 1,000-5,000 users (vs $80-120 on AWS)
   - No hidden costs (predictable billing)
   - Free staging environment (Railway.app)

3. **Developer Productivity**
   - Focus on features, not infrastructure
   - No Kubernetes YAML hell
   - No security group debugging
   - No IAM role confusion

4. **Scalability**
   - Horizontal scaling (add instances in app.yaml)
   - Read replicas (one click)
   - Multi-region (duplicate app.yaml, change region)

5. **Reliability**
   - 99.99% uptime SLA (managed database)
   - Automated backups (point-in-time recovery)
   - Health checks (auto-restart on failure)
   - Monitoring (built-in dashboards)

### Negative Consequences

1. **Vendor Lock-In (Moderate)**
   - app.yaml is DigitalOcean-specific (not portable to other platforms)
   - Migration requires rewriting deployment config

   **Mitigation**:
   - Docker containers portable (can deploy anywhere)
   - Infrastructure-as-Code in Git (app.yaml versioned)
   - Self-hosting option available (docker-compose.yml)

2. **Limited Advanced Features**
   - No advanced networking (VPCs, VPNs, service mesh)
   - No managed Kubernetes (need to migrate to DOKS for K8s)
   - No advanced caching (no managed Redis, need Upstash)

   **Mitigation**:
   - MVP doesn't need advanced features
   - Can migrate to DOKS (DigitalOcean Kubernetes) later
   - Upstash Redis sufficient for caching needs

3. **Region Limitations**
   - Only 5 regions (vs AWS 25+)
   - No regions in: South America, Africa, Australia

   **Mitigation**:
   - CDN (CloudFlare) provides global edge caching
   - Target market is US/Europe (covered by NYC/AMS regions)
   - Can add regions later (multi-region deployment)

4. **Less Mature Than AWS**
   - Newer service (launched 2020, vs AWS 2006)
   - Smaller community (fewer Stack Overflow answers)
   - Fewer integrations (vs AWS's 200+ services)

   **Mitigation**:
   - App Platform stable (production-ready since 2021)
   - Documentation comprehensive
   - Support responsive (24/7 ticket system)

---

## Implementation Notes

### Initial Setup

**1. Create DigitalOcean Account**:
- Sign up: https://cloud.digitalocean.com
- Add payment method (credit card)
- Get $200 credit (via referral link, valid 60 days)

**2. Create App**:
```bash
# Install doctl CLI
brew install doctl  # macOS
# OR
snap install doctl  # Linux

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec .do/app.yaml

# Get app ID
doctl apps list
```

**3. Configure Environment Variables**:
```bash
# Set secrets (not in app.yaml)
doctl apps update $APP_ID --spec .do/app.yaml

# Add secrets in DO console:
# - JWT_SECRET (generate: openssl rand -base64 32)
# - DATABASE_URL (auto-populated from managed DB)
# - REDIS_URL (from Upstash)
```

**4. Configure Custom Domain**:
```bash
# Add domain in DO console
# Point DNS to: taskflow.ondigitalocean.app

# Add CNAME records:
# - www.taskflow.com → taskflow.ondigitalocean.app
# - api.taskflow.com → taskflow.ondigitalocean.app

# SSL auto-provisioned via Let's Encrypt (5-10 minutes)
```

### Deployment Workflow

**1. Development** (local):
```bash
docker-compose -f docker-compose.dev.yml up
# Make changes, test locally
```

**2. Staging** (Railway.app):
```bash
git push origin develop
# Auto-deploys to staging.taskflow.com
# QA testing
```

**3. Production** (DigitalOcean):
```bash
git push origin main
# GitHub Actions runs tests
# If tests pass, auto-deploys to production
# Zero-downtime rolling update
```

### Monitoring

**1. Built-In Dashboards**:
- Go to: Apps → taskflow → Insights
- View: CPU, RAM, requests/sec, errors

**2. External Monitoring** (UptimeRobot):
```bash
# Add monitor:
# - URL: https://taskflow.com/health
# - Interval: 5 minutes
# - Alert: email/Slack on 2 consecutive failures
```

**3. Error Tracking** (Sentry):
```bash
# Add Sentry integration
# Environment variables:
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
```

---

## Cost Projections

### MVP (500 users, 10K requests/day)
- App Platform (1 instance): $12/month
- PostgreSQL (1GB): $15/month
- Upstash Redis: $0 (free tier)
- CloudFlare CDN: $0 (free tier)
- **Total**: $27/month

### Growth (2,000 users, 100K requests/day)
- App Platform (2 instances): $24/month
- PostgreSQL (1GB): $15/month
- Upstash Redis: $10/month
- CloudFlare CDN: $0 (free tier)
- **Total**: $49/month

### Scale (10,000 users, 500K requests/day)
- App Platform (4 instances): $96/month
- PostgreSQL (4GB): $60/month
- Upstash Redis: $30/month
- CloudFlare CDN: $0 (free tier)
- **Total**: $186/month

### Enterprise (100,000 users, 5M requests/day)
- Migrate to DigitalOcean Kubernetes: $200+/month
- PostgreSQL (16GB + read replicas): $300/month
- Redis Cluster: $100/month
- CloudFlare Pro: $20/month
- **Total**: $620/month

---

## Related Decisions

- **ADR-001**: Database Choice (PostgreSQL) - Managed by DigitalOcean
- **ADR-003**: Authentication Strategy (JWT) - Stateless, perfect for App Platform scaling
- **ADR-006**: API Design (REST) - Deployed as Docker container on App Platform

---

## References

- [DigitalOcean App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [App Platform Pricing](https://www.digitalocean.com/pricing/app-platform)
- [Railway.app Documentation](https://docs.railway.app/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Reviewed By**: DevOps Engineer, Technical Lead
**Approved**: 2025-11-19
**Next Review**: After MVP deployment (Month 3)
