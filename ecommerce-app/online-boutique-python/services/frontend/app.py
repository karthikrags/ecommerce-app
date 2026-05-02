"""Frontend Service - Flask web application for the Online Boutique."""

import os
import uuid
import logging

from flask import Flask, render_template, request, redirect, url_for, session, flash
import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

# Service addresses from environment (matching the YAML)
PRODUCT_CATALOG_SERVICE_ADDR = os.environ.get(
    "PRODUCT_CATALOG_SERVICE_ADDR", "productcatalogservice:3550"
)
CURRENCY_SERVICE_ADDR = os.environ.get(
    "CURRENCY_SERVICE_ADDR", "currencyservice:7000"
)
CART_SERVICE_ADDR = os.environ.get("CART_SERVICE_ADDR", "cartservice:7070")
RECOMMENDATION_SERVICE_ADDR = os.environ.get(
    "RECOMMENDATION_SERVICE_ADDR", "recommendationservice:8080"
)
SHIPPING_SERVICE_ADDR = os.environ.get(
    "SHIPPING_SERVICE_ADDR", "shippingservice:50051"
)
CHECKOUT_SERVICE_ADDR = os.environ.get(
    "CHECKOUT_SERVICE_ADDR", "checkoutservice:5050"
)
AD_SERVICE_ADDR = os.environ.get("AD_SERVICE_ADDR", "adservice:9555")

DEFAULT_CURRENCY = "USD"


# ── gRPC stub helpers ──────────────────────────────────────────────────────────

def _stub(addr, stub_class):
    channel = grpc.insecure_channel(addr)
    return stub_class(channel)


def catalog_stub():
    return _stub(PRODUCT_CATALOG_SERVICE_ADDR, demo_pb2_grpc.ProductCatalogServiceStub)


def currency_stub():
    return _stub(CURRENCY_SERVICE_ADDR, demo_pb2_grpc.CurrencyServiceStub)


def cart_stub():
    return _stub(CART_SERVICE_ADDR, demo_pb2_grpc.CartServiceStub)


def recommendation_stub():
    return _stub(
        RECOMMENDATION_SERVICE_ADDR, demo_pb2_grpc.RecommendationServiceStub
    )


def shipping_stub():
    return _stub(SHIPPING_SERVICE_ADDR, demo_pb2_grpc.ShippingServiceStub)


def checkout_stub():
    return _stub(CHECKOUT_SERVICE_ADDR, demo_pb2_grpc.CheckoutServiceStub)


def ad_stub():
    return _stub(AD_SERVICE_ADDR, demo_pb2_grpc.AdServiceStub)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


def get_currency():
    return session.get("currency", DEFAULT_CURRENCY)


def format_money(money: demo_pb2.Money) -> str:
    """Format a Money proto as a human-readable string."""
    cents = money.nanos // 10_000_000
    return f"{money.currency_code} {money.units}.{cents:02d}"


def convert_price(money: demo_pb2.Money, target_currency: str) -> demo_pb2.Money:
    if money.currency_code == target_currency:
        return money
    return currency_stub().Convert(
        demo_pb2.CurrencyConversionRequest(from_=money, to_code=target_currency)
    )


def get_supported_currencies():
    try:
        resp = currency_stub().GetSupportedCurrencies(demo_pb2.Empty())
        return list(resp.currency_codes)
    except grpc.RpcError:
        return [DEFAULT_CURRENCY]


def get_cart_size(user_id: str) -> int:
    try:
        cart = cart_stub().GetCart(demo_pb2.GetCartRequest(user_id=user_id))
        return sum(item.quantity for item in cart.items)
    except grpc.RpcError:
        return 0


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/_healthz")
def healthz():
    return "ok", 200


@app.route("/")
def home():
    user_id = get_session_id()
    currency = get_currency()

    try:
        products_resp = catalog_stub().ListProducts(demo_pb2.Empty())
        products = []
        for p in products_resp.products:
            converted = convert_price(p.price_usd, currency)
            products.append({"product": p, "price": format_money(converted)})
    except grpc.RpcError as e:
        logger.error("Failed to list products: %s", e)
        products = []

    try:
        ads_resp = ad_stub().GetAds(demo_pb2.AdRequest(context_keys=["clothing"]))
        ads = list(ads_resp.ads)
    except grpc.RpcError:
        ads = []

    return render_template(
        "home.html",
        products=products,
        ads=ads,
        currencies=get_supported_currencies(),
        current_currency=currency,
        cart_size=get_cart_size(user_id),
    )


@app.route("/product/<product_id>")
def product(product_id):
    user_id = get_session_id()
    currency = get_currency()

    try:
        p = catalog_stub().GetProduct(demo_pb2.GetProductRequest(id=product_id))
        converted = convert_price(p.price_usd, currency)
        price_str = format_money(converted)
    except grpc.RpcError as e:
        logger.error("Product not found: %s", e)
        flash("Product not found.", "error")
        return redirect(url_for("home"))

    # Recommendations
    try:
        rec_resp = recommendation_stub().ListRecommendations(
            demo_pb2.ListRecommendationsRequest(
                user_id=user_id, product_ids=[product_id]
            )
        )
        rec_products = []
        for pid in rec_resp.product_ids[:4]:
            try:
                rp = catalog_stub().GetProduct(demo_pb2.GetProductRequest(id=pid))
                rp_price = format_money(convert_price(rp.price_usd, currency))
                rec_products.append({"product": rp, "price": rp_price})
            except grpc.RpcError:
                pass
    except grpc.RpcError:
        rec_products = []

    # Ads
    try:
        ads_resp = ad_stub().GetAds(
            demo_pb2.AdRequest(context_keys=list(p.categories))
        )
        ads = list(ads_resp.ads)
    except grpc.RpcError:
        ads = []

    return render_template(
        "product.html",
        product=p,
        price=price_str,
        recommendations=rec_products,
        ads=ads,
        currencies=get_supported_currencies(),
        current_currency=currency,
        cart_size=get_cart_size(user_id),
    )


@app.route("/cart", methods=["GET"])
def view_cart():
    user_id = get_session_id()
    currency = get_currency()

    try:
        cart = cart_stub().GetCart(demo_pb2.GetCartRequest(user_id=user_id))
    except grpc.RpcError:
        cart = demo_pb2.Cart()

    cart_items = []
    subtotal_units = 0
    subtotal_nanos = 0

    for item in cart.items:
        try:
            p = catalog_stub().GetProduct(demo_pb2.GetProductRequest(id=item.product_id))
            converted = convert_price(p.price_usd, currency)
            item_total = demo_pb2.Money(
                currency_code=currency,
                units=converted.units * item.quantity,
                nanos=converted.nanos * item.quantity,
            )
            subtotal_units += item_total.units
            subtotal_nanos += item_total.nanos
            cart_items.append(
                {
                    "product": p,
                    "quantity": item.quantity,
                    "unit_price": format_money(converted),
                    "total_price": format_money(item_total),
                }
            )
        except grpc.RpcError:
            pass

    # Normalise nanos
    subtotal_units += subtotal_nanos // 1_000_000_000
    subtotal_nanos = subtotal_nanos % 1_000_000_000
    subtotal = demo_pb2.Money(
        currency_code=currency, units=subtotal_units, nanos=subtotal_nanos
    )

    # Shipping estimate
    try:
        quote = shipping_stub().GetQuote(
            demo_pb2.GetQuoteRequest(
                address=demo_pb2.Address(country="US"),
                items=list(cart.items),
            )
        )
        shipping = format_money(convert_price(quote.cost_usd, currency))
    except grpc.RpcError:
        shipping = "N/A"

    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=format_money(subtotal),
        shipping=shipping,
        currencies=get_supported_currencies(),
        current_currency=currency,
        cart_size=sum(item.quantity for item in cart.items),
    )


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    user_id = get_session_id()
    product_id = request.form.get("product_id")
    quantity = int(request.form.get("quantity", 1))

    try:
        cart_stub().AddItem(
            demo_pb2.AddItemRequest(
                user_id=user_id,
                item=demo_pb2.CartItem(product_id=product_id, quantity=quantity),
            )
        )
        flash("Item added to cart!", "success")
    except grpc.RpcError as e:
        logger.error("Failed to add item: %s", e)
        flash("Failed to add item to cart.", "error")

    return redirect(url_for("view_cart"))


@app.route("/cart/empty", methods=["POST"])
def empty_cart():
    user_id = get_session_id()
    try:
        cart_stub().EmptyCart(demo_pb2.EmptyCartRequest(user_id=user_id))
    except grpc.RpcError as e:
        logger.error("Failed to empty cart: %s", e)
    return redirect(url_for("view_cart"))


@app.route("/checkout", methods=["GET"])
def checkout():
    user_id = get_session_id()
    currency = get_currency()
    return render_template(
        "checkout.html",
        currencies=get_supported_currencies(),
        current_currency=currency,
        cart_size=get_cart_size(user_id),
    )


@app.route("/checkout", methods=["POST"])
def place_order():
    user_id = get_session_id()
    f = request.form

    address = demo_pb2.Address(
        street_address=f.get("street_address", ""),
        city=f.get("city", ""),
        state=f.get("state", ""),
        country=f.get("country", "US"),
        zip_code=f.get("zip_code", ""),
    )
    credit_card = demo_pb2.CreditCardInfo(
        credit_card_number=f.get("credit_card_number", "").replace(" ", ""),
        credit_card_cvv=int(f.get("credit_card_cvv", 0)),
        credit_card_expiration_year=int(f.get("credit_card_expiration_year", 2025)),
        credit_card_expiration_month=int(f.get("credit_card_expiration_month", 1)),
    )

    try:
        result = checkout_stub().PlaceOrder(
            demo_pb2.PlaceOrderRequest(
                user_id=user_id,
                user_currency=get_currency(),
                address=address,
                email=f.get("email", ""),
                credit_card=credit_card,
            )
        )
        return render_template(
            "order_confirmation.html",
            order=result.order,
            currencies=get_supported_currencies(),
            current_currency=get_currency(),
            cart_size=0,
        )
    except grpc.RpcError as e:
        logger.error("PlaceOrder failed: %s", e)
        flash(f"Order failed: {e.details()}", "error")
        return redirect(url_for("checkout"))


@app.route("/currency", methods=["POST"])
def set_currency():
    currency = request.form.get("currency", DEFAULT_CURRENCY)
    session["currency"] = currency
    return redirect(request.referrer or url_for("home"))


@app.route("/search")
def search():
    query = request.args.get("q", "")
    currency = get_currency()
    user_id = get_session_id()

    try:
        resp = catalog_stub().SearchProducts(
            demo_pb2.SearchProductsRequest(query=query)
        )
        products = []
        for p in resp.results:
            converted = convert_price(p.price_usd, currency)
            products.append({"product": p, "price": format_money(converted)})
    except grpc.RpcError:
        products = []

    return render_template(
        "search.html",
        query=query,
        products=products,
        currencies=get_supported_currencies(),
        current_currency=currency,
        cart_size=get_cart_size(user_id),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
