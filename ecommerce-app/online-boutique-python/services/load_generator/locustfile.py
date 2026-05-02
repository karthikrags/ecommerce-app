"""Load Generator - simulates user traffic using Locust."""

import os
import random
from locust import HttpUser, task, between

FRONTEND_ADDR = os.environ.get("FRONTEND_ADDR", "http://frontend:80")

PRODUCT_IDS = [
    "OLJCESPC7Z",
    "66VCHSJNUP",
    "1YMWWN1N4O",
    "L9ECAV7KIM",
    "2ZYFJ3GM2N",
    "0PUK6V6EV0",
    "LS4PSXUNUM",
    "9SIQT8TOJO",
    "6E92ZMYYFZ",
]


class ShopUser(HttpUser):
    """Simulates a typical online shopper."""

    wait_time = between(1, 3)
    host = FRONTEND_ADDR

    def on_start(self):
        """Visit home page on start."""
        self.client.get("/")

    @task(10)
    def browse_home(self):
        self.client.get("/", name="home")

    @task(8)
    def view_product(self):
        product_id = random.choice(PRODUCT_IDS)
        self.client.get(f"/product/{product_id}", name="product_page")

    @task(5)
    def add_to_cart(self):
        product_id = random.choice(PRODUCT_IDS)
        self.client.post(
            "/cart/add",
            data={"product_id": product_id, "quantity": random.randint(1, 3)},
            name="add_to_cart",
        )

    @task(3)
    def view_cart(self):
        self.client.get("/cart", name="view_cart")

    @task(2)
    def search(self):
        queries = ["mug", "watch", "tank", "loafer", "jar"]
        self.client.get(f"/search?q={random.choice(queries)}", name="search")

    @task(1)
    def checkout_flow(self):
        # Add item first
        product_id = random.choice(PRODUCT_IDS)
        self.client.post(
            "/cart/add",
            data={"product_id": product_id, "quantity": 1},
            name="add_to_cart",
        )
        # View checkout page
        self.client.get("/checkout", name="checkout_page")
        # Place order
        self.client.post(
            "/checkout",
            data={
                "email": "test@example.com",
                "street_address": "1600 Amphitheatre Pkwy",
                "city": "Mountain View",
                "state": "CA",
                "zip_code": "94043",
                "country": "US",
                "credit_card_number": "4111111111111111",
                "credit_card_cvv": "123",
                "credit_card_expiration_month": "12",
                "credit_card_expiration_year": "2027",
            },
            name="place_order",
        )
