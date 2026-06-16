# BigQuery Unstructured Document Demo

This repository showcases an unstructured data analytics architecture built natively in
BigQuery. It demonstrates how teams can extract observations from unstructured
survey PDFs directly inside BigQuery, join them relationally with core ledgers in place,
and compute benchmarks natively to drive precise, data driven decisions.

- **[Unstructured Data Notebook](unstructured_data_demo.ipynb)**

## Key Features Demonstrated

- **Automated PDF Object Tables:** Ingest unstructured commercial survey PDFs from
  GCS buckets into BigQuery external tables with zero file duplication
  or data movement.
- **SQL Native AI Extraction (Gemini Pro):** Run bulk generative AI extraction queries
  using standard BigQuery Standard SQL table functions to parse unstructured narrative
  paragraphs directly into structured JSON mitigation ratings.
- **Verbatim Lakehouse Persistence:** Transcribe complete document texts straight into
  permanent BigQuery String columns, establishing an immutable legal audit record and
  enabling limitless cost free downstream text exploration without reinvoking multimodal
  models.
- **Joining Historical Tables with New Extractions:** Combine extracted survey metrics directly with
  historical policy ledgers (`policy_id`, `earned_premium`)
  seamlessly inside the data warehouse.
- **Translating Ratings to Numerical Values:** Translate qualitative ratings to discrete
  numerical weights while executing rigorous SQL null conversion for unassessed risks to
  protect cohort average calculations from invalid mathematical distortion.
- **Calculating Performance Averages:** Aggregate historical
  events across primary cause codes to calculate baseline averages and compute
  highly accurate composite scores per account.
- **Analytic Performance Benchmarking:** Execute analytical window partitioning (
  `AVG(...) OVER(PARTITION BY year)`) to compute group baseline averages and instantly
  flag records performing significantly worse than the market baseline (e.g.,
  Performance Index > 100).
- **High Dimensional Semantic Retrieval:** Generate numerical vector float arrays
  natively via `AI.GENERATE_EMBEDDING` and perform cosine vector searches to unearth
  subtle liquid accumulation hazards conceptually, without relying on literal keyword
  matching.
- **Multi Entity Property Graph Analytics:** Construct an ISO GQL Property Graph linking
  Policyholders, Machinery Models, and Risk Control Inspectors to reveal portfolio risk
  accumulations via multi hop pattern matching queries (`MATCH ...`).

## Disclaimer

This is a generic, fictitious demonstration built to illustrate the technical
capabilities of BigQuery, Generative AI, Vector Search, and Property
Graphs. The specific grading scales, calculations, and mathematical methodologies shown
here do not represent real world models, nor are they affiliated with any specific
company.

## Prerequisites

This demonstration is fully unified inside BigQuery Studio (Colab Enterprise). To
execute the SQL pipelines natively in your environment, please ensure:

1. You have a target project ID created and configured.
2. Your user account is assigned BigQuery Job User and Vertex AI User IAM roles.
3. **Mandatory Remote Model Handshake:** When BigQuery establishes an external
   connection (`vertex_ai_conn`), it provisions a unique underlying Connection Service
   Account. For remote Gemini models to execute successfully, you must grant that
   Service Account the **Vertex AI User** (`roles/aiplatform.user`) role in IAM.
4. For executing multimodal BigQuery ML inference (`ML.GENERATE_CONTENT`) over external
   GCS Object Tables, your target project must be assigned an active
   Enterprise reservation.

## Useful Links

- [BigQuery Object Tables Documentation](https://cloud.google.com/bigquery/docs/object-tables)
- [BigQuery Machine Learning (BQML) Reference](https://cloud.google.com/bigquery/docs/bqml-introduction)
- [Vector Search in BigQuery Standard SQL](https://cloud.google.com/bigquery/docs/vector-search)
- [Property Graph Analytics in BigQuery Standard SQL](https://cloud.google.com/bigquery/docs/graph-overview)
