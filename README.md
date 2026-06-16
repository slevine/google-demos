# Google Cloud Data Engineering Demos

This repository contains a collection of hands-on demonstrations for modern data
engineering on Google Cloud.

## Prerequisites

All demos in this repository require the following:

- A Google Cloud Platform (GCP) project with billing enabled.
- The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` CLI)
  installed and authenticated to your project.
- For Python-based demos, [**uv**](https://docs.astral.sh/uv/) is used for package
  management. See individual demo
  guides for details.

## Available Demos

- **[BigQuery & Iceberg Open Lakehouse](./bigquery-iceberg-lakehouse/)**
  - Demonstrates a multi-engine lakehouse using BigQuery and Spark on a single Iceberg
    table.

- **[BigQuery Unstructured Document Demo](./bigquery-unstructured-data/)**
  - Showcases an unstructured data analytics architecture built natively in BigQuery.

- **[Data Engineering Agent Introduction](./data-engineering-agent-intro/)**
  - Shows how to use a conversational AI agent to build a data pipeline from natural
    language prompts.

- **[Dataproc Serverless Performance Benchmark](./dataproc-premium-demo/)**
  - Showcases the performance and cost-efficiency of the Dataproc Serverless Premium
    Tier by comparing it against the Standard Tier on a complex, shuffle-intensive
    workload. 
  - It also includes a **[BigQuery benchmark](./dataproc-premium-demo/notebooks/)** to
    compare performance against external and native tables.

- **[Dataproc Secure Multi-Tenancy](./dataproc-secure-multi-tenancy/)**
  - Demonstrates how to enforce fine-grained data access for multiple users on a
    single, shared Dataproc cluster using service account-based security.
