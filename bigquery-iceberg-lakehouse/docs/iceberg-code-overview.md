
# Using the Demo Classes

This guide explains how to use the `TradeGenerator` (for BigQuery) and `SparkDemo` (for Iceberg) classes to interact with your data lakehouse.

---

## Getting Started: iPython Environment

All Python code examples in this guide should be run within an `iPython` session. Before proceeding, start a session from the **root of this project directory**:

```bash
ipython
```

---

## Part 1: BigQuery Trade Generator (`TradeGenerator`)

This class generates and inserts mock trade data directly into Google BigQuery.

### 1.1. Prerequisites: Set Environment Variables

Before starting, export the following environment variables in your terminal.

```bash
export GOOGLE_PROJECT_ID="your-gcp-project-id"
export BQ_TRADES_DATASET_ID="your-bq-dataset-id"
```

*Replace the placeholder values with your actual BigQuery project and dataset IDs.*

### 1.2. Using the `TradeGenerator` Class

Once inside your iPython session, you can import and use the class as follows.

```python
# 1. Import the class from the src module
from src.bq_demo_functions import TradeGenerator

# 2. Create an instance. This initializes the BigQuery client.
trade_generator = TradeGenerator()

# 3. Call methods on the object.

# Generate a basic batch of trades with realistic timestamps
trade_generator.generate_trades()

# Generate 20 trades with current timestamps
trade_generator.generate_trades(count=20, realistic_timestamps=False)

# Change the target BigQuery table
trade_generator.set_active_table("trades_v2_compliance")

# Generate trades with the expanded CAT compliance schema
trade_generator.generate_updated_trades(count=10)

# Generate a large volume of trades in batches
trade_generator.generate_trades_in_batches(total_trades=5000, batch_size=500)
```

---

## Part 2: Spark Iceberg Demo (`SparkDemo`)

This class provides an interface to query and analyze an Iceberg table on Google Cloud Storage using Spark.

### 2.1. Prerequisites: Set Environment Variable

This class requires the GCS path to your Iceberg warehouse.

```bash
export GCS_WAREHOUSE_PATH="gs://your-iceberg-warehouse-path/"
```

*Replace the placeholder value with the GCS path to your Iceberg warehouse directory.*

### 2.2. Using the `SparkDemo` Class

The pattern is the same: import the class, create an instance, and call its methods.

```python
# 1. Import the class
from src.spark_demo_functions import SparkDemo

# 2. Create an instance. This initializes the Spark session.
#    This may take a minute as it downloads the necessary jars.
spark_demo = SparkDemo()

# 3. Call methods on the object.

# Show the latest 5 trades from the Iceberg table
spark_demo.latest(n=5)

# Get a status summary of the table
spark_demo.status()

# List the table's snapshots
spark_demo.list_snapshots()

# Time-travel to a specific snapshot
# spark_demo.show_trades_at_snapshot("your-snapshot-id-here")

# Show the ML code, dynamically referencing the active table
spark_demo.show_ml_code()

# 4. IMPORTANT: Stop the Spark session when you are done
# This releases the cluster resources.
spark_demo.stop()
```
