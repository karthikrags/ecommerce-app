"""Shipping Service - provides shipping quotes and tracking IDs."""

import os
import logging
import uuid
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_shipping_cost(items) -> demo_pb2.Money:
    """Simple cost model: $5 base + $0.50 per item."""
    total_items = sum(item.quantity for item in items)
    cost_usd = 5.0 + (total_items * 0.50)
    units = int(cost_usd)
    nanos = int(round((cost_usd - units) * 1e9))
    return demo_pb2.Money(currency_code="USD", units=units, nanos=nanos)


class ShippingServicer(demo_pb2_grpc.ShippingServiceServicer):
    def GetQuote(self, request, context):
        logger.info("GetQuote called with %d item types", len(request.items))
        cost = calculate_shipping_cost(request.items)
        return demo_pb2.GetQuoteResponse(cost_usd=cost)

    def ShipOrder(self, request, context):
        logger.info(
            "ShipOrder called: city=%s, items=%d",
            request.address.city,
            len(request.items),
        )
        tracking_id = str(uuid.uuid4()).upper()[:18]
        return demo_pb2.ShipOrderResponse(tracking_id=tracking_id)


def serve():
    port = os.environ.get("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_ShippingServiceServicer_to_server(ShippingServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("ShippingService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
