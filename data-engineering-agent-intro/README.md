# Data Engineering Agent Demo

This demo illustrates the power of Google Cloud's Data Engineering Agent in simplifying
complex data transformation tasks. It shows how the agent can interpret a
conversational, multi step business request to build a production ready data pipeline.
The agent automates the entire workflow, from understanding the initial request to
generating the final, compliant, and analysis ready table.

- **[Full Demo Guide](docs/data-eng-agent-demo.md)**

## Key Features Demonstrated

- **Natural Language to SQL:** Convert conversational requests into production ready SQL
  pipelines.
- **Autonomous Goal Pursuit:** The agent makes its own decisions to fulfill a high-level
  goal.
- **Complex, Multi Step Logic:** The agent can handle iterative, conversational
  workflows to build sophisticated data assets.

### Prerequisites

The BigQuery data engineering agent is not yet publicly available. To express interest
in gaining access, please see
the [official announcement](https://cloud.google.com/blog/products/data-analytics/a-closer-look-at-bigquery-data-engineering-agent?e=48754805).

- **Note:** This demo requires you to first set up the `bigquery-iceberg-lakehouse`
  demo, as it uses its code utilities to generate the necessary source data.
