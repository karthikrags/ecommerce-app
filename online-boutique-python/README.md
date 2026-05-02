# Online Boutique – Python Microservices

A complete Python reimplementation of Google's Online Boutique microservices demo, built with gRPC, Flask, and Redis — ready to build, push to Docker Hub, and deploy to Kubernetes.

## Architecture

```
Browser
  └── frontend (Flask :80)
        ├── productcatalogservice  (gRPC :3550)
        ├── currencyservice        (gRPC :7000)
        ├── cartservice            (gRPC :7070)  ← redis-cart :6379
        ├── recommendationservice  (gRPC :8080)
        ├── shippingservice        (gRPC :50051)
        ├── checkoutservice        (gRPC :5050)
        │     ├── productcatalogservice
        │     ├── currencyservice
        │     ├── cartservice
        │     ├── shippingservice
        │     ├── paymentservice   (gRPC :50051)
        │     └── emailservice     (gRPC :5000 → :8080)
        └── adservice              (gRPC :9555)

loadgenerator (Locust) → frontend
```

## Project layout

```
online-boutique-python/
├── proto/
│   └── demo.proto                  # Single source of truth for all gRPC contracts
├── services/
│   ├── ad_service/
│   ├── cart_service/
│   ├── checkout_service/
│   ├── currency_service/
│   ├── email_service/
│   ├── frontend/
│   ├── load_generator/
│   ├── payment_service/
│   ├── product_catalog_service/
│   ├── recommendation_service/
│   └── shipping_service/
│       Each contains: server.py (or app.py), Dockerfile, requirements.txt
├── k8s/
│   ├── redis-cart.yaml
│   ├── currencyservice.yaml
│   ├── productcatalogservice.yaml
│   ├── cartservice.yaml
│   ├── recommendationservice.yaml
│   ├── shippingservice.yaml
│   ├── paymentservice.yaml
│   ├── emailservice.yaml
│   ├── checkoutservice.yaml
│   ├── adservice.yaml
│   ├── frontend.yaml
│   └── loadgenerator.yaml
└── scripts/
    └── build_and_push.sh           # Build all images and push to Docker Hub
```

## Step 1 — Build & push images to Docker Hub

```bash
# Log in to Docker Hub first
docker login

# Set your username and desired tag
export DOCKER_HUB_USERNAME=yourname
export IMAGE_TAG=v1.0.0

bash scripts/build_and_push.sh
```

The script builds each service with a multi-stage Dockerfile (proto generation happens inside the build), tags it as `yourname/<service>:v1.0.0`, and pushes it.

## Step 2 — Update image references in the manifests

Replace `YOUR_DOCKERHUB_USERNAME` in every `k8s/*.yaml` file with your actual username:

```bash
# Linux / macOS
sed -i 's/YOUR_DOCKERHUB_USERNAME/yourname/g' k8s/*.yaml

# Windows PowerShell
Get-ChildItem k8s\*.yaml | ForEach-Object {
  (Get-Content $_) -replace 'YOUR_DOCKERHUB_USERNAME', 'yourname' | Set-Content $_
}
```

## Step 3 — Deploy to Kubernetes

```bash
kubectl apply -f k8s/
```

Check rollout status:

```bash
kubectl get pods -w
kubectl get services
```

The frontend is exposed via `NodePort 30080`. Access it at:
- **Minikube**: `minikube service frontend-external`
- **Cloud cluster**: use the external IP of `frontend-external`, or change its type to `LoadBalancer` in `k8s/frontend.yaml`

## Kubernetes manifest summary

| File | Resources |
|---|---|
| `redis-cart.yaml` | Deployment, Service |
| `currencyservice.yaml` | ServiceAccount, Deployment, Service |
| `productcatalogservice.yaml` | ServiceAccount, Deployment, Service |
| `cartservice.yaml` | ServiceAccount, Deployment, Service |
| `recommendationservice.yaml` | ServiceAccount, Deployment, Service |
| `shippingservice.yaml` | ServiceAccount, Deployment, Service |
| `paymentservice.yaml` | ServiceAccount, Deployment, Service |
| `emailservice.yaml` | ServiceAccount, Deployment, Service |
| `checkoutservice.yaml` | ServiceAccount, Deployment, Service |
| `adservice.yaml` | ServiceAccount, Deployment, Service |
| `frontend.yaml` | ServiceAccount, Deployment, ClusterIP Service, NodePort Service |
| `loadgenerator.yaml` | ServiceAccount, Deployment (with init container) |

## Teardown

```bash
kubectl delete -f k8s/
```
