import sys
from pathlib import Path

import pandas as pd
import great_expectations as gx

SILVER_PATH = str(Path(__file__).resolve().parent.parent / "data" / "delta" / "silver_orders")


def load_silver_as_pandas() -> pd.DataFrame:
    """Reads the Delta Silver table via PySpark, then converts to pandas
    for Great Expectations (keeps GE usage simple and focused)."""
    from delta import configure_spark_with_delta_pip
    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder
        .appName("QualityGateRead")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    df = spark.read.format("delta").load(SILVER_PATH).toPandas()
    spark.stop()
    return df


def run_quality_gate(df: pd.DataFrame) -> bool:
    """Runs Great Expectations checks. Returns True if ALL pass, False otherwise."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas("silver_orders_source")
    data_asset = data_source.add_dataframe_asset(name="silver_orders_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("silver_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    checks = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="price", min_value=0, strict_min=True),
        gx.expectations.ExpectColumnValuesToBeBetween(column="quantity", min_value=0, strict_min=True),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="product"),
    ]

    print("=== Running Quality Gate checks on Silver ===\n")
    all_passed = True
    for expectation in checks:
        result = batch.validate(expectation)
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} — {expectation.__class__.__name__} (column: {expectation.column})")
        if not result.success:
            all_passed = False

    return all_passed


def main():
    df = load_silver_as_pandas()
    print(f"Loaded {len(df)} rows from Silver.\n")

    passed = run_quality_gate(df)

    print(f"\n{'='*50}")
    if passed:
        print("✅ QUALITY GATE PASSED — pipeline may continue.")
        sys.exit(0)
    else:
        print("❌ QUALITY GATE FAILED — halting pipeline before downstream stages.")
        sys.exit(1)  # non-zero exit code = signal to Airflow to stop the DAG


if __name__ == "__main__":
    main()
