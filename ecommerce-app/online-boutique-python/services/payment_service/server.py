"""Payment Service - processes credit card charges (simulated)."""

import os
import logging
import uuid
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test card numbers that are always accepted
VALID_TEST_CARDS = {
    "4432801561520454",
    "4111111111111111",
    "5500005555555559",
}


def luhn_check(card_number: str) -> bool:
    """Validate card number using the Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13:
        return False
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


class PaymentServicer(demo_pb2_grpc.PaymentServiceServicer):
    def Charge(self, request, context):
        card = request.credit_card
        card_number = card.credit_card_number.replace(" ", "").replace("-", "")
        logger.info(
            "Charge called: amount=%s %d, card=****%s",
            request.amount.currency_code,
            request.amount.units,
            card_number[-4:],
        )

        # Validate card
        if not luhn_check(card_number) and card_number not in VALID_TEST_CARDS:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid credit card number")
            return demo_pb2.ChargeResponse()

        # Validate expiry (basic check)
        if card.credit_card_expiration_year < 2024:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Credit card expired")
            return demo_pb2.ChargeResponse()

        transaction_id = str(uuid.uuid4())
        logger.info("Payment successful: transaction_id=%s", transaction_id)
        return demo_pb2.ChargeResponse(transaction_id=transaction_id)


def serve():
    port = os.environ.get("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("PaymentService listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
