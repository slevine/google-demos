# Dataproc Serverless Performance Benchmark

This demo showcases the performance and cost-efficiency of the Dataproc Serverless
Premium Tier by comparing it against the Standard Tier on a complex, shuffle-intensive
workload.

- **[Full Demo Guide](./docs/dataproc-premium-demo.md)**

## Benchmark Overview

The benchmark executes an identical PySpark job on both tiers to measure the
improvements in runtime, resource utilization, and cost. For the tested
workload, the Premium Tier is approximately **2.85x faster** and consumes
**50% fewer** billable resources (DCUs).

- **[Dataproc Serverless Official Documentation](https://cloud.google.com/dataproc-serverless/docs/guides/native-query-execution)**

### Bonus: BigQuery Benchmark

We also include a [notebook](./notebooks/bigquery_benchmark.ipynb) to
benchmark **BigQuery** against this same dataset. It allows you to compare the
performance of:

- **BigLake External Tables**: Querying GCS data directly (zero-copy).
- **Native BigQuery Tables**: Querying data loaded into BigQuery's managed storage.

