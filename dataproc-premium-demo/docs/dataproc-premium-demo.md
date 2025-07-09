# Demo Guide: Dataproc Serverless Performance Benchmark

This document provides a complete walkthrough for benchmarking the Dataproc Serverless
Standard Tier against the Premium Tier with the [Native Query Engine (NQE)][1] enabled.

---

## Table of Contents

- [1. Prerequisites and Configuration](#1-prerequisites-and-configuration)
- [2. Execution Steps](#2-execution-steps)
- [3. Compare Results](#3-compare-results)
- [4. Teardown](#4-teardown)

---

## 1. Prerequisites and Configuration

This section guides you through preparing your Google Cloud environment for the
benchmark.

### Step 1.1: Enable APIs

Ensure the Dataproc API is enabled in your Google Cloud project.

```shell
gcloud services enable dataproc.googleapis.com
```

### Step 1.2: Set Environment Variables

Open a terminal and set the following environment variables.

**Important:** For `GCS_BUCKET`, provide only the bucket name, not the `gs://` prefix.
Bucket names must be globally unique.

```shell
export GOOGLE_PROJECT_ID="your-gcp-project-id"
export REGION="your-region" # e.g., us-central1
export GCS_BUCKET="your-unique-bucket-name"
export SUBNET="your-subnet-name" # e.g., default
```

### Step 1.3: Create a GCS Bucket

This demo requires a Google Cloud Storage bucket to store scripts, data, and output. The
following command uses the variables you just set to create the bucket.

```shell
gsutil mb -p ${GOOGLE_PROJECT_ID} -l ${REGION} gs://${GCS_BUCKET}
```

### Step 1.4: Verify Quotas

This benchmark requests **84 vCPUs** per job. Ensure your regional quotas for both
`CPUS` (for Standard tier) and `N2_CPUS` (for Premium tier) are sufficient in the
`${REGION}` you selected.

---

## 2. Execution Steps

### Step 2.1: Upload Scripts to GCS

From the root of this project directory, upload the two PySpark scripts to a `scripts`
folder in your GCS bucket. The folder will be created automatically by the copy command.

```shell
# Copy the data generator script
gsutil cp src/data_generator.py gs://${GCS_BUCKET}/scripts/data_generator.py

# Copy the analysis job script
gsutil cp src/complex_analysis_job.py gs://${GCS_BUCKET}/scripts/complex_analysis_job.py
```

### Step 2.2: Generate the Test Dataset

Run the `data_generator.py` script as a Dataproc Serverless batch job. This creates
the ~550GB Parquet dataset required for the benchmark. **Note: This step is
long-running.**

```shell
# Define script and data paths
export GENERATOR_SCRIPT_PATH="gs://${GCS_BUCKET}/scripts/data_generator.py"
export DATA_PATH="gs://${GCS_BUCKET}/dataproc-benchmark-data"

# Submit the data generation job
gcloud dataproc batches submit pyspark ${GENERATOR_SCRIPT_PATH} \
    --project=${GOOGLE_PROJECT_ID} \
    --region=${REGION} \
    --subnet=${SUBNET} \
    --version=2.3 \
    --properties=\
spark.driver.cores=4,\
spark.driver.memory=16g,\
spark.executor.cores=4,\
spark.executor.memory=16g,\
spark.executor.instances=20 \
    -- \
    ${DATA_PATH}
```

### Step 2.3: Run the Standard Tier Benchmark

Execute the complex analysis job on the **Standard Tier** to establish baseline
performance.

```shell
# Define script and output paths
export ANALYSIS_SCRIPT_PATH="gs://${GCS_BUCKET}/scripts/complex_analysis_job.py"
export OUTPUT_PATH_SERVERLESS_STD="gs://${GCS_BUCKET}/dataproc-benchmark-output-serverless-standard"

# Submit the Standard Tier job
gcloud dataproc batches submit pyspark ${ANALYSIS_SCRIPT_PATH} \
    --project=${GOOGLE_PROJECT_ID} \
    --region=${REGION} \
    --subnet=${SUBNET} \
    --version=2.3 \
    --properties=\
spark.driver.cores=4,\
spark.driver.memory=16g,\
spark.executor.cores=4,\
spark.executor.memory=16g,\
spark.executor.instances=20 \
    -- \
    ${DATA_PATH} \
    ${OUTPUT_PATH_SERVERLESS_STD}
```

### Step 2.4: Run the Premium Tier (NQE) Benchmark

Execute the same analysis job on the **Premium Tier** with the Native Query Engine
enabled. The key difference is the addition of the `spark.dataproc` properties.

```shell
# Define output path
export OUTPUT_PATH_SERVERLESS_NQE="gs://${GCS_BUCKET}/dataproc-benchmark-output-serverless-nqe"

# Submit the Premium Tier job with NQE
gcloud dataproc batches submit pyspark ${ANALYSIS_SCRIPT_PATH} \
    --project=${GOOGLE_PROJECT_ID} \
    --region=${REGION} \
    --subnet=${SUBNET} \
    --version=2.3 \
    --properties=\
spark.dataproc.runtimeEngine=native,\
spark.dataproc.driver.compute.tier=premium,\
spark.dataproc.executor.compute.tier=premium,\
spark.driver.cores=4,\
spark.driver.memory=16g,\
spark.executor.cores=4,\
spark.executor.memory=16g,\
spark.executor.instances=20,\
spark.memory.offHeap.size=12g \
    -- \
    ${DATA_PATH} \
    ${OUTPUT_PATH_SERVERLESS_NQE}
```

---

## 3. Compare Results

In the Google Cloud Console, navigate to **Dataproc > Batches** and compare the *
*Monitoring** tabs of the two completed analysis jobs.

- **Total Runtime:** Note the reduction in the "Run time" metric. The Premium Tier job
  is expected to be 2-3x faster.
- **Cost:** Compare the "Approximate DCU usage." The Premium Tier job should show a ~50%
  reduction in consumed resources.
- **Disk Spilling:** Observe the "Disk Bytes Spilled" chart. The Standard Tier run will
  likely show significant data spilling, while the Premium Tier run should show zero.
- **GC Time:** Compare the "Ratio of JVM GC Time to Runtime" chart. The Standard Tier
  run will likely show high and volatile GC activity, while the Premium Tier run should
  be flat and near zero.

---

## 4. Teardown

To avoid ongoing storage costs, you can delete the GCS bucket created for this demo.

**Warning:** This command will permanently delete the entire GCS bucket and all of its
contents.

```shell
gsutil rm -r gs://${GCS_BUCKET}
```

[1]:https://cloud.google.com/dataproc-serverless/docs/guides/native-query-execution
