# Online Boutique – Python Microservices

A complete Python reimplementation of Google's [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo) microservices demo, derived from the Kubernetes manifest in `app.yaml`.

## Architecture

```
Browser
  └── Frontend (Flask :80)
        ├── ProductCatalogService  (gRPC :3550)
        ├── CurrencyService        (gRPC :7000)
        ├── CartService            (gRPC :7070)  ← Redis :6379
        ├── RecommendationService  (gRPC :8080)  ← ProductCatalogService
        ├── ShippingService        (gRPC :50051)
        ├── CheckoutService        (gRPC :5050)
        │     ├── ProductCatalogService
        │     ├── CurrencyService
        │     ├── CartService
        │     ├── ShippingService
        │     ├── PaymentService   (gRPC :50051)
        │     └── EmailService     (gRPC :8080)
        └── AdService              (gRPC :9555)

LoadGenerator (Locust) → Frontend
```

All inter-service communication uses **gRPC** with Protocol Buffers (`proto/demo.proto`).

## Services

| Service | Port | Description |
|---|---|---|
| `frontend` | 80 | Flask web UI |
| `productcatalogservice` | 3550 | Static product catalog |
| `currencyservice` | 7000 | Currency conversion |
| `cartservice` | 7070 | Shopping cart (Redis-backed) |
| `recommendationservice` | 8080 | Product recommendations |
| `shippingservice` | 50051 | Shipping quotes & tracking |
| `paymentservice` | 50051 | Credit card processing (simulated) |
| `emailservice` | 8080 | Order confirmation emails (logged) |
| `checkoutservice` | 5050 | Order orchestration |
| `adservice` | 9555 | Contextual ads |
| `redis-cart` | 6379 | Redis for cart storage |
| `loadgenerator` | — | Locust-based traffic simulator |

## Quick Start

### 1. Generate gRPC stubs

```bash
cd online-boutique-python
bash scripts/generate_proto.sh
```

This generates `genproto/demo_pb2.py` and `genproto/demo_pb2_grpc.py` and copies them into each service's `genproto/` folder.

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

Open http://localhost in your browser.

### 3. Run services locally (without Docker)

Install dependencies for each service and run:

```bash
# Example: run currency service
cd services/currency_service
pip install -r requirements.txt
cp -r ../../genproto .
python server.py
```

## Development

### Proto changes

Edit `proto/demo.proto`, then re-run:

```bash
bash scripts/generate_proto.sh
```

### Load testing

The load generator runs automatically in Docker Compose. To run Locust with its web UI:

```bash
cd services/load_generator
pip install -r requirements.txt
locust -f locustfile.py --host http://localhost
# Open http://localhost:8089
```

## Tech Stack

- **Python 3.12**
- **gRPC / Protocol Buffers** – inter-service communication
- **Flask 3** – frontend web framework
- **Redis 7** – cart storage
- **Locust** – load generation
- **Docker Compose** – local orchestration
