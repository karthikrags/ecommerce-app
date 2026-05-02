"""Product Catalog Service - serves a static list of products."""

import os
import logging
import json
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCTS = [
    {
        "id": "OLJCESPC7Z",
        "name": "Sunglasses",
        "description": "Add a modern touch to your outfits with these sleek aviator sunglasses.",
        "picture": "/static/img/products/sunglasses.jpg",
        "price_usd": {"currency_code": "USD", "units": 19, "nanos": 990000000},
        "categories": ["accessories"],
    },
    {
        "id": "66VCHSJNUP",
        "name": "Tank Top",
        "description": "Perfectly cropped cotton tank, with a scooped neckline.",
        "picture": "/static/img/products/tank-top.jpg",
        "price_usd": {"currency_code": "USD", "units": 18, "nanos": 990000000},
        "categories": ["clothing", "tops"],
    },
    {
        "id": "1YMWWN1N4O",
        "name": "Watch",
        "description": "This gold-tone stainless steel watch is perfect for any occasion.",
        "picture": "/static/img/products/watch.jpg",
        "price_usd": {"currency_code": "USD", "units": 109, "nanos": 990000000},
        "categories": ["accessories"],
    },
    {
        "id": "L9ECAV7KIM",
        "name": "Loafers",
        "description": "A modern take on the classic loafer, with a rubber sole.",
        "picture": "/static/img/products/loafers.jpg",
        "price_usd": {"currency_code": "USD", "units": 89, "nanos": 990000000},
        "categories": ["footwear"],
    },
    {
        "id": "2ZYFJ3GM2N",
        "name": "Hairdryer",
        "description": "This lightweight hairdryer has 3 heat and 2 speed settings.",
        "picture": "/static/img/products/hairdryer.jpg",
        "price_usd": {"currency_code": "USD", "units": 24, "nanos": 990000000},
        "categories": ["hair", "beauty"],
    },
    {
        "id": "0PUK6V6EV0",
        "name": "Candle Holder",
        "description": "This beautiful candle holder will add a cozy touch to your home.",
        "picture": "/static/img/products/candle-holder.jpg",
        "price_usd": {"currency_code": "USD", "units": 18, "nanos": 990000000},
        "categories": ["decor", "home"],
    },
    {
        "id": "LS4PSXUNUM",
        "name": "Salt & Pepper Shakers",
        "description": "These stylish salt and pepper shakers are perfect for any kitchen.",
        "picture": "/static/img/products/salt-and-pepper-shakers.jpg",
        "price_usd": {"currency_code": "USD", "units": 18, "nanos": 490000000},
        "categories": ["kitchen"],
    },
    {
        "id": "9SIQT8TOJO",
        "name": "Bamboo Glass Jar",
        "description": "This bamboo glass jar can hold 57 oz (1.7 L) and is perfect for any kitchen.",
        "picture": "/static/img/products/bamboo-glass-jar.jpg",
        "price_usd": {"currency_code": "USD", "units": 5, "nanos": 490000000},
        "categories": ["kitchen"],
    },
    {
        "id": "6E92ZMYYFZ",
        "name": "Mug",
        "description": "A simple mug with a cozy feel, perfect for morning coffee.",
        "picture": "/static/img/products/mug.jpg",
        "price_usd": {"currency_code": "USD", "units": 8, "nanos": 990000000},
        "categories": ["kitchen"],
    },
]


def dict_to_product(p: dict) -> demo_pb2.Product:
    price = p["price_usd"]
    return demo_pb2.Product(
        id=p["id"],
        name=p["name"],
        description=p["description"],
        picture=p["picture"],
        price_usd=demo_pb2.Money(
            currency_code=price["currency_code"],
            units=price["units"],
            nanos=price["nanos"],
        ),
        categories=p["categories"],
    )


class ProductCatalogServicer(demo_pb2_grpc.ProductCatalogServiceServicer):
    def ListProducts(self, request, context):
        logger.info("ListProducts called")
        return demo_pb2.ListProductsResponse(
            products=[dict_to_product(p) for p in PRODUCTS]
        )

    def GetProduct(self, request, context):
        logger.info("GetProduct called: id=%s", request.id)
        for p in PRODUCTS:
            if p["id"] == request.id:
                return dict_to_product(p)
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"Product {request.id} not found")
        return demo_pb2.Product()

    def SearchProducts(self, request, context):
        logger.info("SearchProducts called: query=%s", request.query)
        query = request.query.lower()
        results = [
            dict_to_product(p)
            for p in PRODUCTS
            if query in p["name"].lower() or query in p["description"].lower()
        ]
        return demo_pb2.SearchProductsResponse(results=results)


def serve():
    port = os.environ.get("PORT", "3550")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_ProductCatalogServiceServicer_to_server(
        ProductCatalogServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("ProductCatalogService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
