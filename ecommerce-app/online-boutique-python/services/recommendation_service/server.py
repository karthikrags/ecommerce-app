"""Recommendation Service - returns product recommendations."""

import os
import logging
import random
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_CATALOG_SERVICE_ADDR = os.environ.get(
    "PRODUCT_CATALOG_SERVICE_ADDR", "productcatalogservice:3550"
)


def get_catalog_stub():
    channel = grpc.insecure_channel(PRODUCT_CATALOG_SERVICE_ADDR)
    return demo_pb2_grpc.ProductCatalogServiceStub(channel)


class RecommendationServicer(demo_pb2_grpc.RecommendationServiceServicer):
    def ListRecommendations(self, request, context):
        logger.info(
            "ListRecommendations: user=%s, products=%s",
            request.user_id,
            request.product_ids,
        )
        try:
            stub = get_catalog_stub()
            response = stub.ListProducts(demo_pb2.Empty())
            all_ids = [p.id for p in response.products]
            # Exclude products already in the request
            filtered = [pid for pid in all_ids if pid not in request.product_ids]
            # Return up to 5 random recommendations
            recommended = random.sample(filtered, min(5, len(filtered)))
            return demo_pb2.ListRecommendationsResponse(product_ids=recommended)
        except grpc.RpcError as e:
            logger.error("Failed to fetch products: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to fetch product catalog")
            return demo_pb2.ListRecommendationsResponse()


def serve():
    port = os.environ.get("PORT", "8080")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_RecommendationServiceServicer_to_server(
        RecommendationServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("RecommendationService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
