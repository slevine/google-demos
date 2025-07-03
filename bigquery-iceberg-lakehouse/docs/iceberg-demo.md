# Demo Guide: BigQuery & Iceberg Open Lakehouse

This document provides a complete walkthrough for demonstrating Google Cloud's open
lakehouse architecture, which uses BigQuery to manage Iceberg tables that are fully
accessible to other engines like Apache Spark.

- You can find an overview of the code [here](iceberg-code-overview.md).

## Demo Prerequisites & Configuration

Before starting, you must define the following three variables. They are required for
the setup and execution of the demo.

- **`GOOGLE_PROJECT_ID`**: Your Google Cloud Project ID.
  - *Example:* `your-project-id`
- **`BQ_TRADES_DATASET_ID`**: The BigQuery dataset where your Iceberg table will be
  registered.
  - *Example:* `trades_lakehouse`
- **`GCS_WAREHOUSE_PATH`**: The path to a folder in a GCS bucket where the Iceberg
  table's data and metadata files will be stored.
  - *Example:* `gs://your-gcs-bucket-name/`

**Important:** You must also enable metadata auto-refresh for your project to
automatically update your Iceberg table metadata snapshot on each table mutation. To
enable metadata auto-refresh,
contact <bigquery-tables-for-apache-iceberg-help@google.com>. EXPORT METADATA costs are
applied on each refresh operation.

- [Metadata auto-refresh](https://cloud.google.com/bigquery/docs/iceberg-tables#create-iceberg-table-snapshots)

---

## Table of Contents

- [1. Initial Table Setup](#1-initial-table-setup)
  - [Step 1.1: Create the BigLake Connection](#step-11-create-the-biglake-connection)
  - [Step 1.2: Create the Iceberg Table](#step-12-create-the-iceberg-table)
- [2. Environment Setup](#2-environment-setup)
  - [Python Environment Setup](#python-environment-setup)
  - [Shell 1: The BigQuery Client](#shell-1-the-bigquery-client)
  - [Shell 2: The Spark Client](#shell-2-the-spark-client)
  - [Shell 3: The GCS Inspector](#shell-3-the-gcs-inspector)
- [3. Demo Execution Flow](#3-demo-execution-flow)
  - [Step 3.1: Write Data with BigQuery](#step-31-write-data-with-bigquery)
  - [Step 3.2: Verify Open Storage](#step-32-verify-open-storage)
  - [Step 3.3: Read Data with Spark](#step-33-read-data-with-spark)
  - [Step 3.4: Perform a Live Schema Migration](#step-34-perform-a-live-schema-migration)
  - [Step 3.5: Write Data with the New Schema](#step-35-write-data-with-the-new-schema)
  - [Step 3.6: Verify Schema Propagation in Spark](#step-36-verify-schema-propagation-in-spark)
  - [Step 3.7: The AI Payoff](#step-37-the-ai-payoff)
- [4. Demo Teardown](#4-demo-teardown)

## 1. Initial Table Setup

This section guides you through creating the necessary Google Cloud resources for the
demo. This includes a **BigLake Connection**, which allows BigQuery to securely access
data in Google Cloud Storage, and the **Iceberg Table** itself.

***

### Step 1.1: Create the BigLake Connection

BigQuery requires a `CONNECTION` resource to read and write data in Google Cloud Storage
on your behalf.

1. **Create the Connection:** Run the following `gcloud` command in your terminal to
   create the connection. You must create the connection in the same region as your
   BigQuery dataset.

   ```shell
   gcloud bigquery connections create biglake-connection \
       --project_id="your-gcp-project-id" \
       --location="your-region" \
       --connection_type=CLOUD_RESOURCE
   ```

2. **Grant Permissions:** The command will output a `serviceAccountId`. This is a unique
   identity for your new connection. You must grant this service account the **Storage
   Object Admin** role (`roles/storage.objectAdmin`) on your GCS bucket so it can manage
   the Iceberg files.

* First, retrieve the service account ID:
    ```shell
    gcloud bigquery connections describe biglake-connection \
        --project_id="your-gcp-project-id" \
        --location="your-region" \
        --format="value(cloudResource.serviceAccountId)"
    ```
* Next, grant the required permission, replacing `your-service-account-id` with the
  output from the previous command and `your-gcs-bucket-name` with your bucket's name.
    ```shell
    gsutil iam ch \
        serviceAccount:your-service-account-id:objectAdmin \
        gs://your-gcs-bucket-name
    ```

- For more details, see the official documentation
  on [creating a Cloud resource connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection).

***

### Step 1.2: Create the Iceberg Table

With the connection in place, you can now create the BigLake table. In the BigQuery UI,
run the following `CREATE TABLE` statement. This creates a table entry in BigQuery that
points to the data and metadata files stored in your GCS bucket.

**Remember to replace all placeholder variables** with your actual project, dataset,
region, and GCS path.

```sql
CREATE
OR REPLACE TABLE `your-gcp-project-id.your-bq-dataset-id.trades` (
    trade_id                STRING    OPTIONS(description="Unique identifier for the trade event."),
    trade_timestamp         TIMESTAMP OPTIONS(description="The exact time the trade was executed."),
    ticker                  STRING    OPTIONS(description="The stock symbol, e.g., GOOG, AAPL."),
    price                   FLOAT64   OPTIONS(description="The price per share at the time of the trade."),
    quantity                INT64     OPTIONS(description="The number of shares traded."),
    trade_side              STRING    OPTIONS(description="The side of the trade: 'BUY' or 'SELL'."),
    executing_account       STRING    OPTIONS(description="The internal account that placed the trade.")
)
WITH CONNECTION `your-gcp-project-id.your-region.biglake-connection`
OPTIONS (
    table_format = 'ICEBERG',
    file_format = 'PARQUET',
    storage_uri = 'gs://your-gcs-bucket-name/trades'
);
```

## 2. Environment Setup

This demo uses **three separate terminal shells** to demonstrate true isolation between
the BigQuery engine, the Spark engine, and the underlying cloud storage. Please prepare
three separate terminal windows before proceeding.

### Python Environment Setup

This project uses `uv` to manage its Python environment and dependencies. `uv` is a
fast, modern Python package manager.

1. **Install `uv`:** If you do not have `uv` installed, please follow
   the [official installation guide](https://github.com/astral-sh/uv#installation).

2. **Create the Virtual Environment:** From the root of this project directory, run the
   following command. This will create a new virtual environment in a `.venv` folder.

   ```shell
   uv venv --python 3.12
   ```

3. **Install Dependencies:** Next, run the `sync` command. This will read the
   `pyproject.toml` file and install all the required libraries (like `pyspark`,
   `google-cloud-bigquery`, etc.) into your new virtual environment.

   ```shell
   uv sync
   ```

Your environment is now ready. The following shell setup steps assume you are running
commands from within this activated environment.

### Shell 1: The BigQuery Client

This shell represents a data platform team using BigQuery to manage the lakehouse.

1. **Set Environment Variables:**

   ```shell
   export GOOGLE_PROJECT_ID="your-gcp-project-id"
   export BQ_TRADES_DATASET_ID="your-bq-dataset-id"
   ```

2. **Start iPython:**

   ```shell
   ipython
   ```

3. **Instantiate the Generator:**

   ```python
   from src.bq_demo_functions import TradeGenerator
   trade_generator = TradeGenerator()
   ```

4. **(Optional) Enable Logging:** To see detailed output from the trade generator,
   especially when creating large volumes of data, run the following snippet in your
   iPython session.

   ```python
   import logging
   import sys

   # Get the logger for the specific module
   bq_logger = logging.getLogger('src.bq_demo_functions')
   bq_logger.setLevel(logging.INFO)

   # Add a handler to write logs to the console if one doesn't exist
   if not bq_logger.handlers:
       handler = logging.StreamHandler(sys.stdout)
       formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
       handler.setFormatter(formatter)
       bq_logger.addHandler(handler)
   ```

### Shell 2: The Spark Client

This shell represents a data science team using Spark to analyze the data. It will
connect to the same Iceberg table without using any BigQuery libraries.

1. **Set Environment Variable:**

   ```shell
   export GCS_WAREHOUSE_PATH="gs://your-gcs-bucket-name/"
   ```

2. **Start iPython:**

   ```shell
   ipython
   ```

3. **Instantiate the Spark Client:**

   ```python
   from src.spark_demo_functions import SparkDemo
   spark_demo = SparkDemo()
   # IMPORTANT: Remember to stop the session when finished: spark_demo.stop()
   ```

### Shell 3: The GCS Inspector

This shell is a standard terminal with the `gcloud` CLI installed and authenticated to
your project. It will be used to directly inspect the objects created in the Google
Cloud Storage bucket, proving that the data is being written in an open format.


## 3. Demo Execution Flow

### Step 3.1: Write Data with BigQuery

In **Shell 1 (the BigQuery Client)**, generate 10 new trades. This simulates a live data
feed writing into the lakehouse via BigQuery.

```python
# In BQ iPython Shell
trade_generator.generate_trades(10, False)
```

You can verify the new rows by querying the table in the BigQuery UI.

### Step 3.2: Verify Open Storage

In **Shell 3 (the GCS Inspector)**, inspect the underlying GCS bucket. This proves that
BigQuery is writing to an open format, not a proprietary silo. The GCS path should match
the `storage_uri` from your `CREATE TABLE` statement.

```shell
# View the newly created Parquet data files.
# This confirms the data is stored in an open format.
gsutil ls -l gs://your-gcs-bucket-name/trades/data/ | sort -k 2 -r | head -n 5

# View the Iceberg metadata file that tracks the table state.
# This JSON file is the source of truth for the table's schema and snapshots.
gsutil ls -l gs://your-gcs-bucket-name/trades/metadata/ | sort -k 2 -r | head -n 5
```

### Step 3.3: Read Data with Spark

Now, in **Shell 2 (the Spark Client)**, read from the same Iceberg table. This
demonstrates multi-engine access with zero ETL or data copies.

```python
# In Spark iPython Shell
spark_demo.latest(10)
```

### Step 3.4: Perform a Live Schema Migration

A common challenge is evolving a table's schema without downtime. In the **BigQuery UI
**, run the following `ALTER TABLE` statement to add a new, complex `STRUCT` for
compliance data.

```sql
-- In BigQuery UI
ALTER TABLE `your-gcp-project-id.your-bq-dataset-id.trades`
    ADD COLUMN cat_compliance STRUCT<
    reporter_id STRING,
    order_event_type STRING,
    handling_instructions STRING,
    session_id STRING,
    reported_timestamp TIMESTAMP
>;
```

The schema change is applied instantly. Next, backfill the new `cat_compliance` column for all historical records using a single `MERGE` statement. This powerful operation applies complex, conditional logic to the entire table in one atomic transaction.

The statement has two parts:
* The `WHEN MATCHED` clause finds all trades where the `ticker` is 'NVDA' and updates them with specific compliance data.
* The `WHEN NOT MATCHED BY SOURCE` clause operates on every other row in the table, updating all trades that are *not* 'NVDA' with a different, historical compliance value.

```sql
-- In BigQuery UI
MERGE INTO `your-gcp-project-id.your-bq-dataset-id.trades` T
    USING (
        -- A rule for NVDA stock
        SELECT 'NVDA' as ticker,
               STRUCT(
                       'CAT_DESK_HFT' as reporter_id,
                       'TRD_POST' as order_event_type,
                       'algorithmic' as handling_instructions,
                       GENERATE_UUID() as session_id,
                       CURRENT_TIMESTAMP() as reported_timestamp
               )      as compliance_data
        FROM (SELECT 1)) S ON T.ticker = S.ticker
    WHEN MATCHED THEN
        UPDATE SET T.cat_compliance = S.compliance_data
    WHEN NOT MATCHED BY SOURCE THEN
UPDATE SET T.cat_compliance = STRUCT(
    'CAT_DESK_LEGACY' as reporter_id,
    'TRD_HISTORICAL' as order_event_type,
    'unspecified' as handling_instructions,
    NULL as session_id,
    NULL as reported_timestamp
    );
```

### Step 3.5: Write Data with the New Schema

The table is fully online. In **Shell 1 (the BigQuery Client)**, generate new trades
that conform to the updated schema.

```python
# In BQ iPython Shell
trade_generator.generate_updated_trades(5)
```

### Step 3.6: Verify Schema Propagation in Spark

Return to **Shell 2 (the Spark Client)**. First, inspect the table schema. Spark will
automatically detect the changes made by BigQuery by reading the updated Iceberg
metadata.

```python
# In Spark iPython Shell
spark_demo.schema()
```

Next, query the data. The output will seamlessly combine the newly generated trades with
the historical records that were just backfilled, providing a single, unified view.

```python
# In Spark iPython Shell
spark_demo.latest(10)
```

### Step 3.7: The AI Payoff

The final step is to show that the new, governed data is immediately available for
advanced use cases like AI and machine learning. In **Shell 2 (the Spark Client)**,
display a code snippet for a feature engineering pipeline.

```python
# In Spark iPython Shell
spark_demo.show_ml_code()
```

This demonstrates that a data science team can use the new `cat_compliance` fields to
build models without delay, turning a compliance requirement into an AI ready dataset in
minutes.

---

## 4. Demo Teardown

To clean up the resources created during this demo, follow these steps.

1. **Stop the Spark Session:** In **Shell 2 (the Spark Client)**, release the cluster
   resources.

   ```python
   # In Spark iPython Shell
   spark_demo.stop()
   ```

2. **Delete the BigQuery Table:** In the **BigQuery UI**, run the following command to
   drop the BigLake table.

   ```sql
   -- In BigQuery UI
   DROP TABLE `your-gcp-project-id.your-bq-dataset-id.trades`;
   ```

3. **Delete the GCS Data:** In **Shell 3 (the GCS Inspector)**, delete the underlying
   data and
   metadata files from Google Cloud Storage.

   ```shell
   # In a plain Bash Shell
   # Warning: This command will permanently delete all data and metadata in the specified GCS path.
   gsutil rm -r gs://your-gcs-bucket-name/trades
   ```
