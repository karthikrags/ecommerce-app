"""Cart Service - stores shopping cart data in Redis."""

import os
import logging
import json
from concurrent import futures

import grpc
import redis
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_ADDR = os.environ.get("REDIS_ADDR", "redis-cart:6379")


def get_redis_client():
    host, port = REDIS_ADDR.rsplit(":", 1)
    return redis.Redis(host=host, port=int(port), decode_responses=True)


class CartServicer(demo_pb2_grpc.CartServiceServicer):
    def __init__(self):
        self.redis = get_redis_client()

    def AddItem(self, request, context):
        logger.info(
            "AddItem: user=%s product=%s qty=%d",
            request.user_id,
            request.item.product_id,
            request.item.quantity,
        )
        key = f"cart:{request.user_id}"
        raw = self.redis.get(key)
        cart = json.loads(raw) if raw else {}
        product_id = request.item.product_id
        cart[product_id] = cart.get(product_id, 0) + request.item.quantity
        self.redis.set(key, json.dumps(cart))
        return demo_pb2.Empty()

    def GetCart(self, request, context):
        logger.info("GetCart: user=%s", request.user_id)
        key = f"cart:{request.user_id}"
        raw = self.redis.get(key)
        cart = json.loads(raw) if raw else {}
        items = [
            demo_pb2.CartItem(product_id=pid, quantity=qty)
            for pid, qty in cart.items()
        ]
        return demo_pb2.Cart(user_id=request.user_id, items=items)

    def EmptyCart(self, request, context):
        logger.info("EmptyCart: user=%s", request.user_id)
        self.redis.delete(f"cart:{request.user_id}")
        return demo_pb2.Empty()


def serve():
    port = os.environ.get("PORT", "7070")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_CartServiceServicer_to_server(CartServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("CartService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
