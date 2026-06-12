# BigQuery Commercial Underwriting & Actuarial Document Intelligence Demo

This repository showcases an advanced unstructured data analytics and actuarial
risk scoring architecture built natively on Google Cloud. It demonstrates how
commercial Property and Casualty underwriting teams can unlock critical risk
control observations from unstructured survey PDFs directly inside BigQuery,
join them relationally with core financial ledgers in place, and compute
portfolio premium benchmarks natively to drive precise, data driven renewal
decisions.

- **[Unstructured Data Intelligence Notebook](unstructured_data_intelligence_demo.ipynb)**

## Key Features Demonstrated

- **Automated PDF Object Tables:** Ingest unstructured commercial survey PDFs
  from Google Cloud Storage buckets into BigQuery external tables with zero file
  duplication or data movement.
- **SQL Native AI Extraction (Gemini Pro):** Run bulk generative AI extraction
  queries using standard BigQuery Standard SQL table functions to parse
  unstructured narrative paragraphs directly into structured JSON mitigation
  ratings.
- **Verbatim Lakehouse Persistence:** Transcribe complete document texts
  straight into permanent BigQuery String columns, establishing an immutable
  legal audit record and enabling limitless cost free downstream text
  exploration without reinvoking multimodal models.
- **In Place Relational Ledger Joining:** Combine extracted survey metrics
  directly with core transactional policy and claims ledgers (`policy_id`,
  `earned_premium`) seamlessly inside the data warehouse.
- **Actuarial Grade Translation & Nulling:** Translate qualitative ratings to
  discrete numerical weights while executing rigorous SQL null conversion for
  unassessed risks to protect cohort average calculations from invalid
  mathematical distortion.
- **Historical Loss Distribution Weighting:** Aggregate historical commercial
  injury claims across primary cause codes to calculate portfolio loss weights
  and compute highly accurate composite safety scores per account.
- **SQL Analytic Underwriting Relativities:** Execute analytical window
  partitioning (`AVG(...) OVER(PARTITION BY policy_year)`) to compute peer
  baseline indices and instantly flag high exposure accounts performing worse
  than market baseline relativities.
- **High Dimensional Semantic Retrieval:** Generate numerical vector float
  arrays natively via `AI.GENERATE_EMBEDDING` and perform cosine vector searches
  to unearth subtle liquid accumulation hazards conceptually, without relying on
  literal keyword matching.
- **Multi Entity Property Graph Analytics:** Construct an ISO GQL Property Graph
  linking Policyholders, Machinery Models, and Risk Control Inspectors to reveal
  portfolio risk accumulations via multi hop pattern matching queries
  (`MATCH ...`).

## Prerequisites

This demonstration is fully unified inside BigQuery Studio (Colab Enterprise).
To execute the SQL pipelines natively in your Google Cloud environment, please
ensure:

1. You have a target Google Cloud project ID created and configured.
2. Your user account is assigned BigQuery Job User and Vertex AI User IAM roles.
3. **Mandatory Remote Model Handshake:** When BigQuery establishes an external
   connection (`vertex_ai_conn`), it provisions a unique underlying Connection
   Service Account. For remote Gemini models to execute successfully, you must
   grant that Service Account the **Vertex AI User** (`roles/aiplatform.user`)
   role in IAM.
4. For executing multimodal BigQuery ML inference (`ML.GENERATE_CONTENT`) over
   external Google Cloud Storage Object Tables, your target project must be
   assigned an active Enterprise reservation.

## Useful Links

- [BigQuery Object Tables Documentation](https://cloud.google.com/bigquery/docs/object-tables)
- [BigQuery Machine Learning (BQML) Reference](https://cloud.google.com/bigquery/docs/bqml-introduction)
- [Vector Search in BigQuery Standard SQL](https://cloud.google.com/bigquery/docs/vector-search)
- [Property Graph Analytics in BigQuery Standard SQL](https://cloud.google.com/bigquery/docs/graph-overview)

## Resource Clean Up

If you wish to remove all resources generated during this workshop to avoid
unexpected Google Cloud billing costs, you can either execute the optional final
clean up cell inside the notebook or run the following tool suite commands in
your terminal:

```bash
# Delete all three primary BigQuery analytical datasets
bq rm -r -f -d my-enterprise-project:enterprise_risk_control
bq rm -r -f -d my-enterprise-project:enterprise_policy
bq rm -r -f -d my-enterprise-project:enterprise_underwriting

# Delete external Vertex AI Cloud Resource connection
bq query --use_legacy_sql=false 'DROP CONNECTION IF EXISTS `my-enterprise-project.us.vertex_ai_conn`;'
```
