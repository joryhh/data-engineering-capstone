import json
import time
from datetime import datetime, UTC

from kafka import KafkaProducer
from pydantic import ValidationError
from schema import OrderEvent

# ── Sample raw data: mix of valid and intentionally broken records ──
RAW_ORDERS = [
    {"order_id": "ORD001", "user_id": "U_A", "product": "Laptop", "price": 1200.00, "quantity": 1},
    {"order_id": "ORD002", "user_id": "U_B", "product": "Mouse", "price": 25.5, "quantity": 2},
    {"order_id": "ORD003", "user_id": "U_C", "product": "", "price": 75.00, "quantity": 1},  # bad: empty product
    {"order_id": "ORD004", "user_id": "U_A", "product": "Headphones", "price": -10, "quantity": 1},  # bad: negative price
    {"order_id": "ORD005", "user_id": "U_D", "product": "Keyboard", "price": 89.99, "quantity": -3},  # bad: negative quantity
]

TOPIC = "orders"
QUARANTINE_LOG = "quarantine.jsonl"


def get_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def quarantine(raw_record: dict, reason: str) -> None:
    """Writes a rejected record + reason to a dead-letter file."""
    entry = {
        "record": raw_record,
        "rejection_reason": reason,
        "quarantined_at": datetime.now(UTC).isoformat(),
    }
    with open(QUARANTINE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  🚫 QUARANTINED {raw_record.get('order_id')}: {reason}")


def main() -> None:
    producer = get_producer()
    accepted, rejected = 0, 0

    for raw in RAW_ORDERS:
        try:
            validated = OrderEvent(**raw)
            producer.send(TOPIC, value=validated.model_dump())
            accepted += 1
            print(f"  ✅ SENT {validated.order_id} -> topic '{TOPIC}'")
        except ValidationError as e:
            reason = e.errors()[0]["msg"]
            quarantine(raw, reason)
            rejected += 1

    producer.flush()
    producer.close()

    print(f"\nDone. Accepted: {accepted}, Quarantined: {rejected}")


if __name__ == "__main__":
    main()
