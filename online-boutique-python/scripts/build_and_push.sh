#!/usr/bin/env bash
# Build all service images and push them to Docker Hub.
#
# Usage:
#   export DOCKER_HUB_USERNAME=yourname
#   export IMAGE_TAG=v1.0.0          # optional, defaults to "latest"
#   bash scripts/build_and_push.sh
#
# Prerequisites:
#   docker login   (run once before this script)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PROTO_FILE="$ROOT_DIR/proto/demo.proto"

: "${DOCKER_HUB_USERNAME:?Please set DOCKER_HUB_USERNAME}"
TAG="${IMAGE_TAG:-latest}"

# Services and their build context paths relative to ROOT_DIR
declare -A SERVICES=(
  [currencyservice]="services/currency_service"
  [productcatalogservice]="services/product_catalog_service"
  [cartservice]="services/cart_service"
  [recommendationservice]="services/recommendation_service"
  [shippingservice]="services/shipping_service"
  [paymentservice]="services/payment_service"
  [emailservice]="services/email_service"
  [checkoutservice]="services/checkout_service"
  [adservice]="services/ad_service"
  [frontend]="services/frontend"
  [loadgenerator]="services/load_generator"
)

echo "Building and pushing images as: $DOCKER_HUB_USERNAME/<service>:$TAG"
echo ""

for svc in "${!SERVICES[@]}"; do
  ctx="$ROOT_DIR/${SERVICES[$svc]}"
  image="$DOCKER_HUB_USERNAME/$svc:$TAG"

  echo "──────────────────────────────────────────"
  echo "▶ Building $image"
  echo "──────────────────────────────────────────"

  # Copy proto into build context so the Dockerfile can access it
  cp "$PROTO_FILE" "$ctx/proto/demo.proto" 2>/dev/null || {
    mkdir -p "$ctx/proto"
    cp "$PROTO_FILE" "$ctx/proto/demo.proto"
  }

  docker build \
    --platform linux/amd64 \
    -t "$image" \
    "$ctx"

  echo "▶ Pushing $image"
  docker push "$image"

  # Clean up copied proto
  rm -f "$ctx/proto/demo.proto"
  rmdir "$ctx/proto" 2>/dev/null || true

  echo "✓ Done: $image"
  echo ""
done

echo "All images pushed successfully."
echo ""
echo "Next step — deploy to Kubernetes:"
echo "  kubectl apply -f k8s/"
