# Kubernetes Migration Considerations

## Overview

This document explores the architectural considerations for scaling the Thumper Counter (Deer Tracking System) from Docker Compose to a horizontally-scaled, Kubernetes-based infrastructure.

**Key Question:** Would we be better served having multiple workers behind a load balancer? What would it take to "refit" our work here to run on Kubernetes-like infrastructure?

---

## Current Architecture (Single Worker Container)

### What We Have Now

- **1 worker container** with 32 concurrent threads
- **Celery pool:** `threads` (not `prefork`)
- **GPU:** Shared across all 32 threads
- **Redis:** Central task queue (already supports multiple workers!)
- **Performance:** 840 images/min (good for single GPU)

### The "Single Point of Failure"

- If worker crashes → processing stops (but queue persists in Redis)
- Restart required to resume
- Limited to 1 GPU's capacity

---

## What It Would Take to Scale Horizontally

### Good News: Already Designed for Horizontal Scaling!

The system is **already designed for horizontal scaling!** Here's why:

#### 1. Celery + Redis Architecture (Already Multi-Worker Ready)

Current `docker-compose.yml`:
```yaml
worker:
  build: ./docker/dockerfiles/Dockerfile.worker
  deploy:
    replicas: 1  # <--- Just change this to 3, 5, 10, etc.
```

**To add more workers RIGHT NOW:**
```bash
# Option 1: Scale existing service
docker-compose up -d --scale worker=3

# Option 2: Add separate worker instances
# Just duplicate the worker service in docker-compose.yml
```

#### 2. What Happens with Multiple Workers?

- **Redis queue:** Shared across all workers (already centralized)
- **Task distribution:** Celery automatically distributes tasks
- **No code changes needed:** Application is already stateless
- **GPU requirement:** Each worker needs GPU access OR use CPU workers

#### 3. Kubernetes Migration Path

**Current → Kubernetes mapping:**

| Docker Compose | Kubernetes Equivalent |
|----------------|----------------------|
| backend | Deployment (3 replicas) |
| worker | Deployment (5 replicas with GPU) |
| db | StatefulSet or managed DB (RDS, Cloud SQL) |
| redis | StatefulSet or managed Redis (ElastiCache, Memorystore) |

**Kubernetes manifest example:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deer-worker
spec:
  replicas: 5  # <--- Scale to 5 workers
  selector:
    matchLabels:
      app: deer-worker
  template:
    metadata:
      labels:
        app: deer-worker
    spec:
      containers:
      - name: worker
        image: thumper_counter-worker:latest
        env:
        - name: REDIS_HOST
          value: "redis-service"
        - name: CELERY_CONCURRENCY
          value: "32"
        resources:
          limits:
            nvidia.com/gpu: 1  # Request 1 GPU per pod
```

---

## GPU Scaling Challenges

### The Bottleneck: GPUs, Not Workers

**Current setup:**
- 1 worker × 32 threads × 1 GPU = 840 images/min
- GPU utilization: 31% (optimal, no contention)

### Scaling Options

#### Option A: Multi-GPU Node (Recommended)

```yaml
# 1 machine with 4 GPUs
# 4 worker pods, each with 1 GPU
replicas: 4
resources:
  limits:
    nvidia.com/gpu: 1
```

- **Throughput:** 840 × 4 = **3,360 images/min**
- **Cost:** 1 multi-GPU instance (e.g., AWS p3.8xlarge)

#### Option B: CPU Workers + GPU Workers (Hybrid)

```yaml
# 10 CPU workers (slow but cheap)
# 2 GPU workers (fast, expensive)
```

- Good for cost optimization
- CPU handles low-priority tasks
- GPU handles real-time/urgent tasks

#### Option C: Serverless GPU (e.g., RunPod, Modal)

```python
# Using Modal.com for serverless GPU
@stub.function(gpu="A100", concurrency=10)
def process_image(image_id):
    # Your detection code
    pass
```

- Auto-scales to demand
- Pay per second of GPU usage
- No infrastructure management

---

## Load Balancer Needs

### Backend API: Yes, Needs Load Balancer

```yaml
# Kubernetes Service (built-in load balancing)
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: LoadBalancer
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
```

### Workers: No Load Balancer Needed!

- Workers pull from Redis queue (pull model, not push)
- Redis is the "load balancer" (task queue)
- No HTTP requests between workers

---

## Migration Effort Estimate

### From Docker Compose → Kubernetes

| Component | Effort | Notes |
|-----------|--------|-------|
| Backend | 2 hours | Convert to Deployment + Service |
| Worker | 3 hours | GPU node selectors, resource limits |
| Database | 1 hour | StatefulSet or use managed DB |
| Redis | 1 hour | StatefulSet or use managed Redis |
| Networking | 2 hours | Ingress, services, DNS |
| Storage | 3 hours | PersistentVolumeClaims for images |
| Monitoring | 4 hours | Prometheus, Grafana, logging |
| **Total** | **16 hours** | **~2 days for basic K8s setup** |

---

## Quick Win: Scale Workers NOW (No K8s Needed)

### Test Multi-Worker Setup Right Now

```bash
# Create 3 worker instances
docker-compose up -d --scale worker=3

# OR edit docker-compose.yml
services:
  worker:
    # ... existing config ...
    deploy:
      replicas: 3  # Run 3 instances
```

### Caveat: GPU Access

- Only works if multiple workers can share GPU
- Or if you have multiple GPUs
- Otherwise workers will compete (slower)

---

## Recommended Architecture for Production

### Small Scale (< 100k images/day)

- Docker Compose with 1-2 workers
- Managed database (RDS/Cloud SQL)
- Managed Redis (ElastiCache)
- Single multi-GPU instance

### Medium Scale (100k - 1M images/day)

- Kubernetes with 5-10 worker pods
- Node pool with GPU nodes
- Horizontal pod autoscaling
- Managed services for DB/Redis

### Large Scale (> 1M images/day)

- Kubernetes + serverless GPU (Modal/RunPod)
- Auto-scaling based on queue depth
- Multi-region deployment
- CDN for image delivery

---

## Bottom Line

### Your System is ALREADY Designed for Horizontal Scaling!

The Celery + Redis architecture is production-grade and used by companies like Instagram, Uber, and Pinterest for exactly this reason.

### Answers to Specific Questions

#### 1. Multiple workers behind load balancer?

- **Workers:** Don't need load balancer (pull from queue)
- **Backend API:** Yes, would benefit from load balancer

#### 2. What would it take to run on Kubernetes?

- **Time:** ~2 days to containerize and deploy
- **Main challenge:** GPU node management
- **Everything else:** Straightforward

#### 3. Immediate action (if you want):

```bash
# Test with 2 workers right now
docker-compose up -d --scale worker=2
```

- See if GPU contention becomes an issue
- Monitor with `docker stats`

---

## Architecture Comparison

### Current: Docker Compose (Single Node)

```
┌─────────────────────────────────────────┐
│          Single Host Machine            │
│                                         │
│  ┌──────────┐  ┌──────────────────┐   │
│  │ Backend  │  │ Worker (32 threads)│   │
│  │ (3 inst) │  │ GPU: RTX 4080     │   │
│  └────┬─────┘  └─────────┬────────┘   │
│       │                   │             │
│  ┌────┴─────┐   ┌────────┴────────┐   │
│  │PostgreSQL│   │     Redis       │   │
│  └──────────┘   └─────────────────┘   │
└─────────────────────────────────────────┘

Throughput: 840 images/min
SPOF: Worker crash = processing stops
```

### Future: Kubernetes (Multi-Node)

```
┌─────────────────────────────────────────────────────┐
│            Kubernetes Cluster                       │
│                                                     │
│  ┌──────────────────────────────────────────────┐ │
│  │         Ingress Load Balancer                │ │
│  └──────────────┬───────────────────────────────┘ │
│                 │                                  │
│  ┌──────────────┴───────────────┐                │
│  │  Backend Pods (3 replicas)   │                │
│  │  - Auto-scaling 1-10         │                │
│  └──────────────┬───────────────┘                │
│                 │                                  │
│  ┌──────────────┴───────────────────────────┐   │
│  │    GPU Node Pool (4 nodes)               │   │
│  │  ┌──────────────────────────────────┐   │   │
│  │  │ Worker Pod 1 (GPU 0, 32 threads) │   │   │
│  │  │ Worker Pod 2 (GPU 1, 32 threads) │   │   │
│  │  │ Worker Pod 3 (GPU 2, 32 threads) │   │   │
│  │  │ Worker Pod 4 (GPU 3, 32 threads) │   │   │
│  │  └──────────────────────────────────┘   │   │
│  └──────────────┬───────────────────────────┘   │
│                 │                                  │
│  ┌──────────────┴───────────────────────────┐   │
│  │  Managed Services (Cloud)                │   │
│  │  - Cloud SQL (PostgreSQL)                │   │
│  │  - ElastiCache (Redis)                   │   │
│  │  - S3/GCS (Image Storage)                │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

Throughput: 3,360 images/min (4× improvement)
Resilience: Worker failure auto-replaced
Auto-scaling: Based on queue depth
```

---

## Migration Checklist

### Phase 1: Preparation (1 day)

- [ ] Create Kubernetes manifests (Deployments, Services, ConfigMaps)
- [ ] Set up Docker registry (Docker Hub, GCR, ECR)
- [ ] Push images to registry
- [ ] Configure secrets (DB credentials, API keys)

### Phase 2: Infrastructure (4 hours)

- [ ] Provision Kubernetes cluster (GKE, EKS, AKS)
- [ ] Create GPU node pool
- [ ] Set up managed PostgreSQL
- [ ] Set up managed Redis
- [ ] Configure persistent volumes for images

### Phase 3: Deployment (4 hours)

- [ ] Deploy database (or connect to managed DB)
- [ ] Deploy Redis (or connect to managed Redis)
- [ ] Deploy backend API (3 replicas)
- [ ] Deploy workers (4 replicas with GPU)
- [ ] Configure Ingress/Load Balancer
- [ ] Set up DNS

### Phase 4: Monitoring (4 hours)

- [ ] Deploy Prometheus
- [ ] Deploy Grafana
- [ ] Configure alerts (Slack, PagerDuty)
- [ ] Set up log aggregation (ELK, Loki)
- [ ] Create dashboards (GPU usage, queue depth, throughput)

### Phase 5: Testing (4 hours)

- [ ] Smoke tests (health checks)
- [ ] Load testing (queue 100k images)
- [ ] Failover testing (kill worker pods)
- [ ] GPU utilization verification
- [ ] Cost analysis

---

## Cost Comparison

### Current Setup (Docker Compose)

| Component | Specs | Monthly Cost |
|-----------|-------|--------------|
| Single server | RTX 4080 Super, 32GB RAM | $0 (existing hardware) |
| **Total** | | **$0/month** |

### Kubernetes Setup (Cloud)

#### Option A: Self-Managed (GKE/EKS)

| Component | Specs | Monthly Cost |
|-----------|-------|--------------|
| Control plane | Managed K8s | $73/month |
| GPU nodes (4×) | p3.2xlarge (V100) | $3,000/month |
| CPU nodes (3×) | t3.medium | $75/month |
| Cloud SQL | PostgreSQL 15 | $200/month |
| ElastiCache | Redis | $50/month |
| Storage | 1TB SSD | $100/month |
| **Total** | | **$3,500/month** |

#### Option B: Serverless GPU (Modal/RunPod)

| Component | Specs | Monthly Cost |
|-----------|-------|--------------|
| Backend | Cloud Run (3 instances) | $50/month |
| Worker | Modal.com (A100, pay-per-use) | $500-1,500/month |
| Cloud SQL | PostgreSQL 15 | $200/month |
| Redis | Upstash (managed) | $50/month |
| Storage | S3/GCS | $100/month |
| **Total** | | **$900-1,900/month** |

**Recommendation:** Unless processing > 1M images/month, current setup is most cost-effective.

---

## When to Migrate to Kubernetes

### Migrate When:

1. **Processing > 100k images/day** consistently
2. **Uptime requirements** > 99.5% (need redundancy)
3. **Multiple GPUs** available (horizontal scaling justified)
4. **Team grows** beyond 1-2 developers (need staging/production separation)
5. **Geographic distribution** needed (multi-region deployments)

### Stay on Docker Compose When:

1. **Current throughput** (840 images/min) is sufficient
2. **Budget-constrained** ($0/month vs $900-3,500/month)
3. **Single developer/team** managing system
4. **Development/testing phase** still ongoing
5. **Local GPU hardware** already owned

---

## Conclusion

The Thumper Counter system has a **solid, production-ready architecture** that scales horizontally by design. The Celery + Redis pattern is battle-tested and used by major tech companies.

**Current state:**
- Already supports multiple workers
- No code changes needed to scale
- Worker restart is only manual intervention needed

**For now:** Docker Compose is perfect for your use case.

**For future:** When you need 3-4× throughput or 99.9% uptime, Kubernetes migration is straightforward (~2 days).

The architecture you've built is exactly right - you've already done the hard work of making it scalable!

---

**Document created:** November 11, 2025
**Author:** Claude Code
**Related docs:** REPROCESSING_GUIDE.md, SPRINT_4_SUMMARY.md
