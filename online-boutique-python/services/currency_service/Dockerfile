FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt grpcio-tools==1.64.1

# Generate proto stubs
COPY proto/demo.proto .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. demo.proto

# ── Runtime image ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy generated stubs + service code
COPY --from=builder /build/demo_pb2.py /build/demo_pb2_grpc.py ./
COPY server.py .

RUN groupadd -g 1000 appgroup && useradd -u 1000 -g appgroup -M appuser
USER appuser

ENV PORT=7000
EXPOSE 7000

CMD ["python", "server.py"]
