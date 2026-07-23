import sys
import pandas as pd

from quality_gate import run_quality_gate

# Deliberately broken data: duplicate order_id, negative price, null product
BAD_DATA = pd.DataFrame([
    {"order_id": "BAD001", "user_id": "U_X", "product": "Item A", "price": 50.0, "quantity": 1},
    {"order_id": "BAD001", "user_id": "U_Y", "product": "Item B", "price": 30.0, "quantity": 1},  # duplicate order_id
    {"order_id": "BAD003", "user_id": "U_Z", "product": None,    "price": -20.0, "quantity": 2},  # null product, negative price
])

if __name__ == "__main__":
    print("=== Intentionally feeding BAD data into the Quality Gate ===\n")
    print(BAD_DATA)
    print()

    passed = run_quality_gate(BAD_DATA)

    if passed:
        print("\n❌ UNEXPECTED: bad data passed the gate (this should not happen).")
        sys.exit(1)
    else:
        print("\n✅ EXPECTED: Quality Gate correctly caught the bad data and would halt the pipeline here.")
        sys.exit(1)  # simulates Airflow seeing a failed task
