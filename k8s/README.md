# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the P&L Demo application.

## Structure

```
k8s/
├── base/                    # Base manifests (shared across environments)
│   ├── namespace.yaml       # Namespace definition
│   ├── configmap.yaml       # Configuration data
│   ├── secret.yaml          # Sensitive data (template)
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── ingress.yaml         # Ingress rules
│   └── kustomization.yaml   # Kustomize base config
├── overlays/
│   ├── dev/                 # Development overrides
│   │   └── kustomization.yaml
│   └── prod/                # Production overrides
│       └── kustomization.yaml
```

## Prerequisites

- Kubernetes cluster (minikube, kind, EKS, AKS, GKE)
- kubectl configured
- Container images pushed to registry

## Quick Start (Local with Minikube)

```bash
# Start minikube
minikube start

# Enable ingress addon
minikube addons enable ingress

# Build and load images locally
eval $(minikube docker-env)
docker build -t pnl-backend:latest ./backend
docker build -t pnl-frontend:latest ./frontend

# Apply dev configuration
kubectl apply -k k8s/overlays/dev

# Check status
kubectl get pods -n pnl-demo
kubectl get services -n pnl-demo

# Access the application
minikube service frontend -n pnl-demo
```

## Key Concepts

### Namespace
Isolates resources for this application:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pnl-demo
```

### Deployment
Manages pod replicas and rolling updates:
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
```

### Service
Exposes pods internally (ClusterIP) or externally (LoadBalancer):
```yaml
apiVersion: v1
kind: Service
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8000
```

### ConfigMap
Non-sensitive configuration:
```yaml
apiVersion: v1
kind: ConfigMap
data:
  DATABASE_HOST: postgres
```

### Secret
Sensitive data (base64 encoded):
```yaml
apiVersion: v1
kind: Secret
data:
  POSTGRES_PASSWORD: cGFzc3dvcmQ=  # base64 encoded
```

### Ingress
HTTP routing rules:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  rules:
    - host: pnl-demo.local
      http:
        paths:
          - path: /api
            backend:
              service:
                name: backend
```

## Production Deployment

```bash
# Apply production configuration
kubectl apply -k k8s/overlays/prod

# Scale deployments
kubectl scale deployment backend --replicas=3 -n pnl-demo

# Check rollout status
kubectl rollout status deployment/backend -n pnl-demo
```

## Useful Commands

```bash
# View logs
kubectl logs -f deployment/backend -n pnl-demo

# Execute into pod
kubectl exec -it deployment/backend -n pnl-demo -- /bin/bash

# Port forward for debugging
kubectl port-forward svc/backend 8000:8000 -n pnl-demo

# View resource usage
kubectl top pods -n pnl-demo

# Describe pod issues
kubectl describe pod <pod-name> -n pnl-demo
```

## Monitoring

For production, consider adding:
- Prometheus for metrics
- Grafana for dashboards
- Loki for log aggregation
- Jaeger for distributed tracing
