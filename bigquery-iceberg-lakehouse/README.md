# BigQuery & Iceberg Open Lakehouse Demo

This demo showcases a modern, open lakehouse architecture on Google Cloud. It
demonstrates how a single Apache Iceberg table can be seamlessly managed by BigQuery for
data warehousing tasks while also being used by Apache Spark for data science workloads,
all with no data duplication. The guide walks through writing data with BigQuery,
reading it with Spark, performing a live schema migration, and showing how the changes
are instantly available across both engines.

- **[Full Demo Guide](docs/iceberg-demo.md)**
- **[Code Overview](docs/iceberg-code-overview.md)**

## Key Features Demonstrated

- **Multi-Engine Access:** Write with BigQuery, read with Spark, on the same table.
- **Zero Copy Integration:** No ETL or data duplication is required between engines.
- **Transactional Integrity:** Perform reliable, atomic operations like `MERGE` and
  `ALTER TABLE` across multiple engines.
- **Live Schema Evolution:** Perform `ALTER TABLE` operations in BigQuery that are
  instantly and safely reflected in Spark.
- **Open Standards:** All data is stored in open-source Apache Parquet and Iceberg
  formats in a GCS bucket.

## Prerequisites

This project uses `uv` to manage its Python environment. Please see
the [full demo guide](docs/iceberg-demo.md) for detailed setup instructions.

## Useful Links

- [Enhancing BigLake for Iceberg lakehouses](https://cloud.google.com/blog/products/data-analytics/enhancing-biglake-for-iceberg-lakehouses)
- [BigQuery Iceberg Tables Documentation](https://cloud.google.com/bigquery/docs/iceberg-tables)