"""
Generates large-scale, skewed datasets for the Dataproc NQE benchmark.

This script creates two Parquet tables:
1.  `customer_master`: A dimension table with 50 million unique customers.
2.  `sales_transactions`: A fact table with 20 billion transactions, partitioned by
    the 'region' column to simulate a realistic data layout.
"""

import sys
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    array,
    col,
    element_at,
    floor,
    lit,
    monotonically_increasing_id,
    rand,
    to_timestamp,
    when,
)
from pyspark.sql.types import IntegerType, StringType


def _generate_customer_data(spark: SparkSession, num_customers: int) -> DataFrame:
    """
    Generates a DataFrame representing the customer master table.

    Args:
        spark: The active SparkSession.
        num_customers: The number of customers to generate.

    Returns:
        A DataFrame with the customer schema.
    """
    print(f"--> Generating customer_master table with {num_customers:,} rows...")

    states = array(
        [lit(s) for s in ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI"]]
    )
    num_states = 10

    df = spark.range(num_customers).withColumn("id", monotonically_increasing_id())

    return (
        df.withColumn("customer_id", col("id"))
        .withColumn("name", col("id").cast(StringType()) + "_name")
        .withColumn(
            "state",
            # Skew the data distribution heavily towards CA.
            when(rand() < 0.9, "CA").otherwise(
                element_at(states, (floor(rand() * (num_states - 1)) + 1).cast("int"))
            ),
        )
        .withColumn(
            "signup_date",
            # Generate a random timestamp within a one-year window.
            to_timestamp((lit(1577836800) + (rand() * 31536000)).cast("timestamp")),
        )
        .select("customer_id", "name", "state", "signup_date")
    )


def _generate_sales_data(
    spark: SparkSession, num_transactions: int, num_customers: int
) -> DataFrame:
    """
    Generates a DataFrame representing the sales transactions fact table.

    Args:
        spark: The active SparkSession.
        num_transactions: The number of transactions to generate.
        num_customers: The total number of unique customers to reference.

    Returns:
        A DataFrame with the sales schema.
    """
    print(f"--> Generating sales_transactions table with {num_transactions:,} rows...")

    regions = array([lit(r) for r in ["West", "South", "Northeast", "Midwest"]])
    num_partitions = 4000

    df = spark.range(0, num_transactions, 1, num_partitions).withColumn(
        "id", monotonically_increasing_id()
    )

    return (
        df.withColumn("transaction_id", col("id"))
        .withColumn("customer_id", floor(rand() * num_customers))
        .withColumn("product_id", floor(rand() * 100).cast(IntegerType()))
        .withColumn(
            "region",
            # Deterministically assign region based on customer_id.
            element_at(regions, ((col("customer_id") % 4) + 1).cast("int")),
        )
        .withColumn("transaction_amount", (rand() * 490) + 10)  # Values from 10-500
        .withColumn(
            "timestamp",
            # Generate a random timestamp within a two-year window.
            to_timestamp((lit(1640995200) + (rand() * 63072000)).cast("timestamp")),
        )
        .select(
            "transaction_id",
            "customer_id",
            "product_id",
            "region",
            "transaction_amount",
            "timestamp",
        )
    )


def generate_test_data(spark: SparkSession, output_path: str) -> None:
    """
    Coordinates the generation of all benchmark datasets.

    Args:
        spark: The active SparkSession.
        output_path: The GCS path to write the Parquet tables.
    """
    num_customers = 50_000_000
    num_transactions = 20_000_000_000

    # Generate and write customer data
    customer_df = _generate_customer_data(spark, num_customers)
    customer_df.cache()
    customer_df.count()  # Trigger cache

    customer_master_path = f"{output_path}/customer_master.parquet"
    customer_df.write.mode("overwrite").parquet(customer_master_path)
    print(f"--> Successfully wrote customer_master to {customer_master_path}")

    # Generate and write sales data
    transactions_df = _generate_sales_data(spark, num_transactions, num_customers)
    sales_transactions_path = f"{output_path}/sales_transactions.parquet"
    transactions_df.write.partitionBy("region").mode("overwrite").parquet(
        sales_transactions_path
    )
    print(f"--> Successfully wrote sales_transactions to {sales_transactions_path}")

    customer_df.unpersist()
    print("--> Data generation complete.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: data_generator.py <gcs_output_path>", file=sys.stderr)
        sys.exit(-1)

    gcs_output_path = sys.argv[1]

    spark = SparkSession.builder.appName(
        "Dataproc NQE Benchmark: Data Generation"
    ).getOrCreate()

    generate_test_data(spark, gcs_output_path)

    spark.stop()
