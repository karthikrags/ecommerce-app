"""Currency Service - converts between currencies using fixed exchange rates."""

import os
import logging
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Exchange rates relative to USD
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50,
    "CAD": 1.36,
    "AUD": 1.53,
    "CHF": 0.90,
    "CNY": 7.24,
    "INR": 83.12,
    "BRL": 4.97,
}


def money_to_usd(money: demo_pb2.Money) -> float:
    """Convert a Money proto to a USD float."""
    amount = money.units + money.nanos / 1e9
    rate = EXCHANGE_RATES.get(money.currency_code, 1.0)
    return amount / rate


def usd_to_money(usd: float, currency_code: str) -> demo_pb2.Money:
    """Convert a USD float to a Money proto in the target currency."""
    rate = EXCHANGE_RATES.get(currency_code, 1.0)
    converted = usd * rate
    units = int(converted)
    nanos = int(round((converted - units) * 1e9))
    return demo_pb2.Money(currency_code=currency_code, units=units, nanos=nanos)


class CurrencyServicer(demo_pb2_grpc.CurrencyServiceServicer):
    def GetSupportedCurrencies(self, request, context):
        logger.info("GetSupportedCurrencies called")
        return demo_pb2.GetSupportedCurrenciesResponse(
            currency_codes=list(EXCHANGE_RATES.keys())
        )

    def Convert(self, request, context):
        logger.info(
            "Convert called: %s %s -> %s",
            request.from_.units,
            request.from_.currency_code,
            request.to_code,
        )
        usd = money_to_usd(request.from_)
        result = usd_to_money(usd, request.to_code)
        return result


def serve():
    port = os.environ.get("PORT", "7000")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_CurrencyServiceServicer_to_server(CurrencyServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("CurrencyService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
