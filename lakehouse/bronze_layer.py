import shutil
from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)

BRONZE_PATH = "./data/delta/bronze_orders"

# Same raw data shape as the Kafka producer sent — including a late-arriving
# duplicate order_id (ORD001) to prove MERGE/upsert logic later in Silver.
RAW_ORDERS = [
    {"order_id": "ORD001", "user_id": "U_A", "product": "Laptop",     "price": 1200.00, "quantity": 1},
    {"order_id": "ORD002", "user_id": "U_B", "product": "Mouse",      "price": 25.5,    "quantity": 2},
    {"order_id": "ORD006", "user_id": "U_E", "product": "Monitor",    "price": 340.0,   "quantity": 1},
    {"order_id": "ORD007", "user_id": "U_F", "product": "Desk Chair", "price": 210.0,   "quantity": 2},
]

BRONZE_SCHEMA = StructType([
    StructField("order_id",  StringType(),  nullable=False),
    StructField("user_id",   StringType(),  nullable=True),
    StructField("product",   StringType(),  nullable=True),
    StructField("price",     DoubleType(),  nullable=True),
    StructField("quantity",  IntegerType(), nullable=True),
])


def create_spark_session() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("BronzeLayer")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def main() -> None:
    Path("./data/delta").mkdir(parents=True, exist_ok=True)

    spark = create_spark_session()
    df = spark.createDataFrame(RAW_ORDERS, schema=BRONZE_SCHEMA)

    print("\n=== Raw data landing into Bronze (as-is, no cleaning) ===")
    df.show(truncate=False)

    (df.write
       .format("delta")
       .mode("append")   # append-only: Bronze never overwrites history
       .save(BRONZE_PATH))

    print(f"✅ Bronze write complete -> {BRONZE_PATH}")
    print(f"   Row count in this batch: {df.count()}")

    spark.stop()


if __name__ == "__main__":
    main()
