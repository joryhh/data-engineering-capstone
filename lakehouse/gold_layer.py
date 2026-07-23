from pathlib import Path
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = str(Path(__file__).resolve().parent.parent / "data" / "delta" / "silver_orders")
GOLD_PATH   = str(Path(__file__).resolve().parent.parent / "data" / "delta" / "gold_product_summary")


def create_spark_session() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("GoldLayer")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def main() -> None:
    spark = create_spark_session()

    silver_df = spark.read.format("delta").load(SILVER_PATH)
    print("=== Silver (input to Gold) ===")
    silver_df.orderBy("order_id").show(truncate=False)

    # ── Real aggregate: NOT a copy of Silver ────────────────────────
    gold_df = (
        silver_df
        .withColumn("revenue", F.col("price") * F.col("quantity"))
        .groupBy("product")
        .agg(
            F.count("order_id").alias("total_orders"),
            F.sum("quantity").alias("total_units_sold"),
            F.round(F.sum("revenue"), 2).alias("total_revenue"),
            F.round(F.avg("price"), 2).alias("avg_price"),
        )
        .orderBy(F.desc("total_revenue"))
    )

    print("\n=== Gold (genuine aggregate: revenue per product) ===")
    gold_df.show(truncate=False)

    (gold_df.write
        .format("delta")
        .mode("overwrite")   # Gold reflects the latest full summary each run
        .save(GOLD_PATH))

    print(f"✅ Gold write complete -> {GOLD_PATH}")

    spark.stop()


if __name__ == "__main__":
    main()
