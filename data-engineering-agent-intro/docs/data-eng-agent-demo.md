# Demo Guide: Data Engineering Agent

## Introduction

A governed, AI ready dataset is the essential first step for any data driven
organization. This guide demonstrates the future of the data engineering workflow by
using an AI agent to turn complex business requests into production ready tables in
minutes.

An AI agent is a system that proactively and autonomously pursues a goal. Unlike a
simple tool, it makes its own decisions and can interact in a conversational style to
complete a task.

Reference:

- [Official Announcement](https://cloud.google.com/blog/products/data-analytics/a-closer-look-at-bigquery-data-engineering-agent?e=48754805)

## Prerequisites: Create the Source Table

This demo requires a large source table of historical trade data. The following steps
will guide you through creating and populating it.

### Step 1: Create the BigQuery Table

In the BigQuery UI, run the following `CREATE TABLE` statement. This will create the
table with the correct schema. Remember to replace the placeholder variables with your
actual project, dataset, and GCS path.

> **Note:** This step requires a BigLake connection to be configured in your project.
> Please see
> the [guide in the bigquery-iceberg-lakehouse demo](../../bigquery-iceberg-lakehouse/docs/iceberg-demo.md#step-11-create-the-biglake-connection)
> for instructions on creating one.

```sql
CREATE
OR REPLACE TABLE `your-gcp-project-id.your-bq-dataset-id.trades_history` (
    trade_id                STRING    OPTIONS(description="Unique identifier for the trade event."),
    trade_timestamp         TIMESTAMP OPTIONS(description="The exact time the trade was executed."),
    ticker                  STRING    OPTIONS(description="The stock symbol, e.g., GOOG, AAPL."),
    price                   FLOAT64   OPTIONS(description="The price per share at the time of the trade."),
    quantity                INT64     OPTIONS(description="The number of shares traded."),
    trade_side              STRING    OPTIONS(description="The side of the trade: 'BUY' or 'SELL'."),
    executing_account       STRING    OPTIONS(description="The internal account that placed the trade."),
    cat_compliance          STRUCT<
        reporter_id STRING,
        order_event_type STRING,
        handling_instructions STRING,
        session_id STRING,
        reported_timestamp TIMESTAMP
    >
)
WITH CONNECTION `your-gcp-project-id.your-region.biglake-connection`
OPTIONS (
    table_format = 'ICEBERG',
    file_format = 'PARQUET',
    storage_uri = 'gs://your-gcs-bucket-name/trades_history'
);
```

### Step 2: Generate Mock Data

This demo requires a large source table of historical trades. To populate it, we will
use the same `TradeGenerator` utility available in the **BigQuery & Iceberg Open
Lakehouse** demo.

From your terminal, navigate into the `bigquery-iceberg-lakehouse` directory and start
an `iPython` shell from there (after activating its virtual environment). Then, run the
following Python code. This script connects to your BigQuery project and generates 1
million mock trades in efficient batches into the `trades_history` table.

```python
from src.bq_demo_functions import TradeGenerator

# Initialize the generator from the other demo's src directory
trade_generator = TradeGenerator()

# IMPORTANT: Set the active table to the 'trades_history' table we created
# for this agent demo.
trade_generator.set_active_table("trades_history")

# Generate 1 million trades in batches of 20,000. This may take a few minutes.
trade_generator.generate_trades_in_batches(total_trades=1000000, batch_size=20000)
```

## Demo 1: Generating a Daily Summary Report

This first demo illustrates how the agent handles a common, single step analytics
request. The goal is to process a large historical trade ledger from an Iceberg table
and distill it into key daily metrics for each stock: the total traded volume and the
volume weighted average price (VWAP).

This task would normally be a ticket in an engineer's backlog. With the agent, the
entire workflow from understanding the request for 'VWAP' to generating the SQL pipeline
is automated in seconds.

### Step 1: Provide the Business Request

In the agent's interface, provide the following natural language prompt:

```
I need a summary report from the trades_lakehouse.trades_history table. Can you create a new table called analytics.daily_ticker_summary that shows the total volume (SUM of quantity) and the volume weighted average price for each ticker for each day? The columns should be trade_date, ticker, total_volume, and vwap
```

### Step 2: Review the Result

The agent will process this request and generate a pipeline to create a powerful, pre
aggregated summary table in the `analytics` schema. This new table enables analysts to
build BI dashboards and perform time series analysis much more efficiently.

## Demo 2: Multi-Step Anomaly Detection Pipeline

Data analysis is often an iterative conversation. This demo showcases a more complex,
multi step scenario: building a pipeline to proactively identify statistically
significant trading anomalies for a compliance review.

### Step 1: Establish a Statistical Baseline

To find an anomaly, one must first define what is normal. The first request asks the
agent to create a table that establishes the statistical baseline for every stock by
calculating its average price and standard deviation for each trading day. This provides
the essential context for the agent to understand what constitutes a significant
deviation.

Provide the following prompt to the agent:

```
I need to find anomalous trades in the trades_lakehouse.trades_history table. First, please create a new table in the analytics dataset named daily_ticker_baselines that calculates the average price and the standard deviation of the price for each ticker on each given day.
```

### Step 2: Calculate a Z-Score for Each Trade

With the baseline table created, the next step is to join it back to the original trades
and calculate a Z-score for every transaction. The Z-score is a standard statistical
measure that quantifies how far a data point is from its average. The agent already has
this domain knowledge and does not need the formula to be provided.

Provide the following conversational prompt:

```
Great. Now, join the original trades_lakehouse.trades_history data with the analytics.daily_ticker_baselines table. Create a new table named analytics.trade_zscores that includes all original columns plus a new column called price_z_score. This score should be the trade's price minus the daily average price, all divided by the daily standard deviation.
```

The agent will generate a pipeline to enrich every trade with this unified "anomaly
score," allowing for fair comparisons of outliers across different stocks.

### Step 3: Filter for Significant Outliers

With an anomaly score attached to every trade, the final step is to filter for only the
most significant outliers, for example, any trade with a Z-score greater than 1.5, and
save them to a final table for review.

Provide the final prompt:

```
Excellent. For the final step, please select all columns from analytics.trade_zscores where the absolute value of the price_z_score is greater than 1.5. Save these significant outliers to a new table named analytics.trades_for_compliance_review
```

This final step filters out the noise and creates a clean, prioritized table named
`trades_for_compliance_review` for a compliance officer. The entire process, from a high
level business goal to a production ready data asset, is completed through a simple
conversation.

## Conclusion

Across both of these examples, the agent demonstrates its ability to understand a
business goal, whether it's a single request for a VWAP report or a multi step
conversation to find outliers. This capability isn't just about generating code faster;
it's about fundamentally shrinking the development cycle between a business question and
a production ready data asset.
