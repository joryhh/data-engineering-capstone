from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)

BRONZE_PATH = "./data/delta/bronze_orders"
SILVER_PATH = "./data/delta/silver_orders"

# Simulates a late-arriving UPDATE for ORD001 (quantity corrected 1 -> 3)
# plus one brand-new order — proves MERGE handles both update AND insert.
INCOMING_UPDATES = [
    {"order_id": "ORD001", "user_id": "U_A", "product": "Laptop", "price": 1200.00, "quantity": 3},
    {"order_id": "ORD008", "user_id": "U_G", "product": "Webcam", "price": 55.0, "quantity": 1},
]

SCHEMA = StructType([
    StructField("order_id",  StringType(),  nullable=False),
    StructField("user_id",   StringType(),  nullable=True),
    StructField("product",   StringType(),  nullable=True),
    StructField("price",     DoubleType(),  nullable=True),
    StructField("quantity",  IntegerType(), nullable=True),
])


def create_spark_session() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("SilverLayer")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def main() -> None:
    spark = create_spark_session()

    # ── Step 1: read raw Bronze data ──────────────────────────────
    bronze_df = spark.read.format("delta").load(BRONZE_PATH)
    print("=== Bronze (before Silver MERGE) ===")
    bronze_df.orderBy("order_id").show(truncate=False)

    # ── Step 2: first run only — seed Silver from Bronze ──────────
    if not DeltaTable.isDeltaTable(spark, SILVER_PATH):
        bronze_df.write.format("delta").mode("overwrite").save(SILVER_PATH)
        print(f"Silver table initialized from Bronze -> {SILVER_PATH}")

    # ── Step 3: build the incoming batch (schema-enforced) ────────
    incoming_df = spark.createDataFrame(INCOMING_UPDATES, schema=SCHEMA)

    # ── Step 4: real Delta Lake MERGE keyed on order_id ────────────
    silver_table = DeltaTable.forPath(spark, SILVER_PATH)

    (silver_table.alias("target")
        .merge(
            incoming_df.alias("source"),
            "target.order_id = source.order_id"   # business key
        )
        .whenMatchedUpdateAll()    # existing order_id -> UPDATE
        .whenNotMatchedInsertAll() # new order_id -> INSERT
        .execute())

    print("\n✅ MERGE complete.")

    # ── Step 5: prove it worked ────────────────────────────────────
    result_df = spark.read.format("delta").load(SILVER_PATH)
    print("\n=== Silver (after MERGE) ===")
    result_df.orderBy("order_id").show(truncate=False)

    print("Check ORD001 above: quantity should now be 3 (updated, not duplicated).")
    print("Check ORD008 above: should be newly inserted.")

    spark.stop()


if __name__ == "__main__":
    main()
