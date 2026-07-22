import json
from kafka import KafkaConsumer

TOPIC = "orders"


def main() -> None:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=5000,  # stop after 5s of no new messages
    )

    print(f"Listening on topic '{TOPIC}' ...\n")
    count = 0
    for message in consumer:
        order = message.value
        print(f"  📥 RECEIVED offset={message.offset} partition={message.partition} -> {order}")
        count += 1

    print(f"\nDone. Total messages consumed: {count}")


if __name__ == "__main__":
    main()
