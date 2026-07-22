from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

SILVER_PATH = "./data/delta/silver_orders"


def create_spark_session() -> SparkSession:
    builder = (
        SparkSession.builder
        .appName("ProveSchemaEnforcement")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def main() -> None:
    spark = create_spark_session()

    # Deliberately WRONG schema: price/quantity as strings with a totally
    # unexpected extra column, to prove Delta rejects mismatched writes.
    bad_schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("unexpected_column", StringType(), True),
    ])
    bad_df = spark.createDataFrame(
        [("ORD999", "this schema does not match Silver at all")],
        schema=bad_schema,
    )

    print("Attempting to write a schema-mismatched batch into Silver...\n")
    try:
        (bad_df.write
            .format("delta")
            .mode("append")
            # NOTE: no mergeSchema option -> enforcement stays strict
            .save(SILVER_PATH))
        print("❌ UNEXPECTED: the bad write was allowed through.")
    except Exception as e:
        print("✅ Delta Lake correctly REJECTED the schema-mismatched write.")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Message (truncated): {str(e)[:300]}")

    spark.stop()


if __name__ == "__main__":
    main()
