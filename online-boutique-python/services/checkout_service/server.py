"""Checkout Service - orchestrates the full order placement flow."""

import os
import logging
import uuid
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_CATALOG_SERVICE_ADDR = os.environ.get(
    "PRODUCT_CATALOG_SERVICE_ADDR", "productcatalogservice:3550"
)
SHIPPING_SERVICE_ADDR = os.environ.get(
    "SHIPPING_SERVICE_ADDR", "shippingservice:50051"
)
PAYMENT_SERVICE_ADDR = os.environ.get(
    "PAYMENT_SERVICE_ADDR", "paymentservice:50051"
)
EMAIL_SERVICE_ADDR = os.environ.get("EMAIL_SERVICE_ADDR", "emailservice:5000")
CURRENCY_SERVICE_ADDR = os.environ.get(
    "CURRENCY_SERVICE_ADDR", "currencyservice:7000"
)
CART_SERVICE_ADDR = os.environ.get("CART_SERVICE_ADDR", "cartservice:7070")


def _stub(addr, stub_class):
    channel = grpc.insecure_channel(addr)
    return stub_class(channel)


class CheckoutServicer(demo_pb2_grpc.CheckoutServiceServicer):
    def PlaceOrder(self, request, context):
        order_id = str(uuid.uuid4())
        logger.info("PlaceOrder: user=%s order_id=%s", request.user_id, order_id)

        # 1. Get cart
        cart_stub = _stub(CART_SERVICE_ADDR, demo_pb2_grpc.CartServiceStub)
        cart = cart_stub.GetCart(demo_pb2.GetCartRequest(user_id=request.user_id))
        if not cart.items:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Cart is empty")
            return demo_pb2.PlaceOrderResponse()

        # 2. Get product prices and convert to user currency
        catalog_stub = _stub(
            PRODUCT_CATALOG_SERVICE_ADDR, demo_pb2_grpc.ProductCatalogServiceStub
        )
        currency_stub = _stub(
            CURRENCY_SERVICE_ADDR, demo_pb2_grpc.CurrencyServiceStub
        )

        order_items = []
        total = demo_pb2.Money(currency_code=request.user_currency, units=0, nanos=0)

        for cart_item in cart.items:
            product = catalog_stub.GetProduct(
                demo_pb2.GetProductRequest(id=cart_item.product_id)
            )
            # Convert price to user currency
            converted_price = currency_stub.Convert(
                demo_pb2.CurrencyConversionRequest(
                    from_=product.price_usd, to_code=request.user_currency
                )
            )
            # Multiply by quantity
            item_cost = demo_pb2.Money(
                currency_code=request.user_currency,
                units=converted_price.units * cart_item.quantity,
                nanos=converted_price.nanos * cart_item.quantity,
            )
            order_items.append(
                demo_pb2.OrderItem(item=cart_item, cost=item_cost)
            )
            total = demo_pb2.Money(
                currency_code=request.user_currency,
                units=total.units + item_cost.units,
                nanos=total.nanos + item_cost.nanos,
            )

        # Normalise nanos overflow
        total = demo_pb2.Money(
            currency_code=total.currency_code,
            units=total.units + total.nanos // 1_000_000_000,
            nanos=total.nanos % 1_000_000_000,
        )

        # 3. Get shipping quote
        shipping_stub = _stub(
            SHIPPING_SERVICE_ADDR, demo_pb2_grpc.ShippingServiceStub
        )
        shipping_quote = shipping_stub.GetQuote(
            demo_pb2.GetQuoteRequest(
                address=request.address, items=list(cart.items)
            )
        )
        shipping_cost = currency_stub.Convert(
            demo_pb2.CurrencyConversionRequest(
                from_=shipping_quote.cost_usd, to_code=request.user_currency
            )
        )

        # 4. Charge payment
        charge_total = demo_pb2.Money(
            currency_code=total.currency_code,
            units=total.units + shipping_cost.units,
            nanos=total.nanos + shipping_cost.nanos,
        )
        payment_stub = _stub(
            PAYMENT_SERVICE_ADDR, demo_pb2_grpc.PaymentServiceStub
        )
        charge_result = payment_stub.Charge(
            demo_pb2.ChargeRequest(
                amount=charge_total, credit_card=request.credit_card
            )
        )
        logger.info("Payment charged: transaction_id=%s", charge_result.transaction_id)

        # 5. Ship order
        ship_result = shipping_stub.ShipOrder(
            demo_pb2.ShipOrderRequest(
                address=request.address, items=list(cart.items)
            )
        )

        # 6. Empty cart
        cart_stub.EmptyCart(demo_pb2.EmptyCartRequest(user_id=request.user_id))

        # 7. Send confirmation email
        order_result = demo_pb2.OrderResult(
            order_id=order_id,
            shipping_tracking_id=ship_result.tracking_id,
            shipping_cost=shipping_cost,
            shipping_address=request.address,
            items=order_items,
        )
        email_stub = _stub(EMAIL_SERVICE_ADDR, demo_pb2_grpc.EmailServiceStub)
        email_stub.SendOrderConfirmation(
            demo_pb2.SendOrderConfirmationRequest(
                email=request.email, order=order_result
            )
        )

        logger.info("Order placed successfully: order_id=%s", order_id)
        return demo_pb2.PlaceOrderResponse(order=order_result)


def serve():
    port = os.environ.get("PORT", "5050")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_CheckoutServiceServicer_to_server(CheckoutServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("CheckoutService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
