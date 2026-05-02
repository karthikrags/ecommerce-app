"""Email Service - sends order confirmation emails (simulated via logging)."""

import os
import logging
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailServicer(demo_pb2_grpc.EmailServiceServicer):
    def SendOrderConfirmation(self, request, context):
        order = request.order
        logger.info(
            "Sending order confirmation to %s | order_id=%s | tracking=%s | "
            "shipping_cost=%s %d | items=%d",
            request.email,
            order.order_id,
            order.shipping_tracking_id,
            order.shipping_cost.currency_code,
            order.shipping_cost.units,
            len(order.items),
        )
        # In a real service this would send an actual email via SMTP / SendGrid / SES
        print(f"\n{'='*60}")
        print(f"ORDER CONFIRMATION EMAIL")
        print(f"{'='*60}")
        print(f"To: {request.email}")
        print(f"Order ID: {order.order_id}")
        print(f"Tracking ID: {order.shipping_tracking_id}")
        print(
            f"Shipping Cost: {order.shipping_cost.currency_code} "
            f"{order.shipping_cost.units}.{order.shipping_cost.nanos // 10_000_000:02d}"
        )
        print(f"Items:")
        for item in order.items:
            print(
                f"  - {item.item.product_id} x{item.item.quantity} "
                f"@ {item.cost.currency_code} {item.cost.units}"
            )
        print(f"{'='*60}\n")
        return demo_pb2.Empty()


def serve():
    port = os.environ.get("PORT", "8080")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_EmailServiceServicer_to_server(EmailServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("EmailService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
