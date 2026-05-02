"""Ad Service - returns context-aware ads."""

import os
import logging
import random
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADS = {
    "clothing": [
        demo_pb2.Ad(redirect_url="/product/66VCHSJNUP", text="Tank Tops for Summer!"),
    ],
    "accessories": [
        demo_pb2.Ad(redirect_url="/product/1YMWWN1N4O", text="Stylish Watches on Sale"),
        demo_pb2.Ad(redirect_url="/product/OLJCESPC7Z", text="Sunglasses – 20% Off"),
    ],
    "footwear": [
        demo_pb2.Ad(redirect_url="/product/L9ECAV7KIM", text="New Loafers Arrived"),
    ],
    "hair": [
        demo_pb2.Ad(redirect_url="/product/2ZYFJ3GM2N", text="Best Hairdryers 2025"),
    ],
    "decor": [
        demo_pb2.Ad(redirect_url="/product/0PUK6V6EV0", text="Cozy Home Decor"),
    ],
    "kitchen": [
        demo_pb2.Ad(redirect_url="/product/LS4PSXUNUM", text="Kitchen Essentials"),
        demo_pb2.Ad(redirect_url="/product/9SIQT8TOJO", text="Bamboo Jars – Eco Friendly"),
    ],
}

FALLBACK_ADS = [
    demo_pb2.Ad(redirect_url="/product/6E92ZMYYFZ", text="Cozy Mugs for Every Morning"),
    demo_pb2.Ad(redirect_url="/", text="Shop the Latest Arrivals"),
]


class AdServicer(demo_pb2_grpc.AdServiceServicer):
    def GetAds(self, request, context):
        logger.info("GetAds called: context_keys=%s", list(request.context_keys))
        ads = []
        for key in request.context_keys:
            ads.extend(ADS.get(key.lower(), []))

        if not ads:
            ads = FALLBACK_ADS

        # Return up to 2 random ads
        selected = random.sample(ads, min(2, len(ads)))
        return demo_pb2.AdResponse(ads=selected)


def serve():
    port = os.environ.get("PORT", "9555")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_AdServiceServicer_to_server(AdServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("AdService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
