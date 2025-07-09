"""
Runs a shuffle-intensive Spark job to benchmark Dataproc Serverless performance.

This script is designed to be fully compatible with the Dataproc Serverless
Native Query Engine (NQE), using only supported operations.
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, countDistinct, sum, when


def run_complex_analysis(
    spark: SparkSession, input_path: str, output_path: str
) -> None:
    """
    Executes a multi-stage Spark job involving joins, transformations, and aggregations.

    Args:
        spark: The active SparkSession.
        input_path: The GCS path to the source Parquet data.
        output_path: The GCS path to write the final results.
    """
    # 1. Read Source Data
    # Read the two main tables for the analysis.
    print("--> Reading source data...")
    sales_df = spark.read.parquet(f"{input_path}/sales_transactions.parquet")
    customers_df = spark.read.parquet(f"{input_path}/customer_master.parquet")

    # 2. Initial Join
    # Join the sales and customer tables to create a unified view.
    # The customer table is small, but we let the optimizer choose the strategy.
    print("--> Performing initial join...")
    joined_df = sales_df.join(customers_df, "customer_id", "inner")

    # Cache the joined DataFrame to optimize subsequent actions.
    joined_df.cache()
    initial_count = joined_df.count()
    print(f"    Initial joined DataFrame has {initial_count} rows.")

    # 3. Customer Segmentation
    # Apply a simple transformation to categorize customers. This is a lightweight,
    # map-side operation.
    print("--> Performing customer segmentation...")
    segmented_df = joined_df.withColumn(
        "customer_tier",
        when((col("state") == "CA") | (col("state") == "NY"), "Gold").otherwise(
            "Silver"
        ),
    )

    # 4. Final Aggregation
    # This is the most shuffle-intensive stage, performing multiple aggregations
    # to create the final summary report.
    print("--> Performing final aggregation...")
    final_summary_df = (
        segmented_df.groupBy("region", "state", "customer_tier")
        .agg(
            sum("transaction_amount").alias("total_sales"),
            avg("transaction_amount").alias("average_sale_amount"),
            countDistinct("customer_id").alias("distinct_customers"),
        )
        .orderBy(col("total_sales").desc())
    )

    # 5. Write Final Results
    # Write the aggregated data back to GCS in Parquet format.
    print(f"--> Writing final results to {output_path}/final_summary...")
    final_summary_df.write.mode("overwrite").parquet(f"{output_path}/final_summary")

    joined_df.unpersist()
    print("--> Complex analysis job finished.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: complex_analysis_job.py <gcs_input_path> <gcs_output_path>",
            file=sys.stderr,
        )
        sys.exit(-1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    spark = SparkSession.builder.appName(
        "Dataproc NQE Benchmark: Complex Analysis"
    ).getOrCreate()

    run_complex_analysis(spark, input_path, output_path)

    spark.stop()
