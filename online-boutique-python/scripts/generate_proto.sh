#!/usr/bin/env bash
# Generates Python gRPC stubs from demo.proto and copies them to each service.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="$ROOT_DIR/proto"
OUT_DIR="$ROOT_DIR/genproto"

echo "Installing grpcio-tools..."
pip install --quiet grpcio-tools==1.64.1 protobuf==5.27.2

echo "Generating Python stubs into $OUT_DIR ..."
mkdir -p "$OUT_DIR"
python -m grpc_tools.protoc \
  -I "$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_DIR/demo.proto"

# Fix relative imports in generated grpc file (grpc_tools quirk)
sed -i 's/^import demo_pb2/import demo_pb2/' "$OUT_DIR/demo_pb2_grpc.py" 2>/dev/null || true

echo "Copying stubs to each service..."
SERVICES=(
  currency_service
  product_catalog_service
  cart_service
  recommendation_service
  shipping_service
  payment_service
  email_service
  checkout_service
  ad_service
  frontend
)

for svc in "${SERVICES[@]}"; do
  SVC_DIR="$ROOT_DIR/services/$svc/genproto"
  mkdir -p "$SVC_DIR"
  cp "$OUT_DIR"/*.py "$SVC_DIR/"
  echo "  ✓ $svc"
done

echo "Done! Proto stubs generated and distributed."
