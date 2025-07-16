# Demo Guide: Dataproc Secure Multi-Tenancy

This document provides a complete walkthrough for demonstrating Dataproc's Service
Account-based Secure Multi-tenancy feature. This allows multiple users to share a
single cluster, while ensuring each user can only access the specific Google Cloud
Storage (GCS) data they are authorized to view.

## Demo Prerequisites & Configuration

Before starting, you must define the following variables. They are required for the
setup and execution of the demo.

- **`GOOGLE_PROJECT_ID`**: Your Google Cloud Project ID.
  - _Example:_ `your-project-id`
- **`ORG_DOMAIN`**: The domain associated with your Google Cloud organization.
  - _Example:_ `your-company.com`
- **`FINANCE_USER_EMAIL`**: The email of the user who will have access to only the
  finance data.
  - _Example:_ `analyst@your-company.com`
- **`MARKETING_USER_EMAIL`**: The email of the user who will have access to only the
  marketing data.
  - _Example:_ `data-engineer@your-company.com`

---

## Table of Contents

- [1. Initial Environment Setup](#1-initial-environment-setup)
  - [Step 1.1: Enable Google Cloud APIs](#step-11-enable-google-cloud-apis)
  - [Step 1.2: Create Service Accounts](#step-12-create-service-accounts)
- [2. Infrastructure and Data Setup](#2-infrastructure-and-data-setup)
  - [Step 2.1: Create GCS Buckets](#step-21-create-gcs-buckets)
  - [Step 2.2: Create and Upload Sample Data](#step-22-create-and-upload-sample-data)
- [3. IAM and Cluster Configuration](#3-iam-and-cluster-configuration)
  - [Step 3.1: Grant Bucket-Level Permissions](#step-31-grant-bucket-level-permissions)
  - [Step 3.2: Grant Core Multi-Tenancy Permissions](#step-32-grant-core-multi-tenancy-permissions)
  - [Step 3.3: Create the Secure Dataproc Cluster](#step-33-create-the-secure-dataproc-cluster)
  - [Step 3.4: Configure Staging and Temp Bucket Permissions](#step-34-configure-staging-and-temp-bucket-permissions)
- [4. Demo Execution Flow](#4-demo-execution-flow)
  - [Step 4.1: Test as the Finance User](#step-41-test-as-the-finance-user)
  - [Step 4.2: Test as the Marketing User](#step-42-test-as-the-marketing-user)
- [5. Demo Teardown](#5-demo-teardown)

---

## 1. Initial Environment Setup

This section guides you through preparing your Google Cloud project and creating the
necessary service accounts.

### Step 1.1: Enable Google Cloud APIs

Run the following command to enable all the necessary APIs for the demo.

```shell
gcloud services enable \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    dataproc.googleapis.com \
    compute.googleapis.com \
    iamcredentials.googleapis.com \
    storage.googleapis.com
```

### Step 1.2: Create Service Accounts

We need three service accounts: one for the finance user's jobs, one for the marketing
user's jobs, and one for the Dataproc cluster's virtual machines.

```shell
# Set environment variables for the service accounts
export FINANCE_SA="sa-finance-viewer@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com"
export MARKETING_SA="sa-marketing-viewer@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com"
export DATAPROC_VM_SA="dataproc-vm-sa-simple@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com"

# Create the service accounts
gcloud iam service-accounts create sa-finance-viewer --display-name="Finance Data Viewer SA"
gcloud iam service-accounts create sa-marketing-viewer --display-name="Marketing Data Viewer SA"
gcloud iam service-accounts create dataproc-vm-sa-simple --display-name="Simple Dataproc VM SA"
```

---

## 2. Infrastructure and Data Setup

This section covers the creation of GCS buckets and the sample data needed for the
demo.

### Step 2.1: Create GCS Buckets

We will create two separate GCS buckets to hold the finance and marketing data.

```shell
# Set environment variables for the buckets
export FINANCE_BUCKET="gs://simple-bucket-finance-${GOOGLE_PROJECT_ID}"
export MARKETING_BUCKET="gs://simple-bucket-marketing-${GOOGLE_PROJECT_ID}"
export REGION="us-central1"

# Create the buckets
gsutil mb -p $GOOGLE_PROJECT_ID -l ${REGION} ${FINANCE_BUCKET}
gsutil mb -p $GOOGLE_PROJECT_ID -l ${REGION} ${MARKETING_BUCKET}
```

### Step 2.2: Create and Upload Sample Data

Create two simple text files and upload them to their respective buckets.

```shell
echo "This is the simplified finance data." | gsutil cp - ${FINANCE_BUCKET}/finance.txt
echo "This is the simplified marketing data." | gsutil cp - ${MARKETING_BUCKET}/marketing.txt
```

---

## 3. IAM and Cluster Configuration

This is the core of the setup, where we configure the permissions and create the secure
cluster.

### Step 3.1: Grant Bucket-Level Permissions

Grant each data-specific service account `objectViewer` access only to its
corresponding data bucket.

```shell
gsutil iam ch "serviceAccount:${FINANCE_SA}:objectViewer" ${FINANCE_BUCKET}
gsutil iam ch "serviceAccount:${MARKETING_SA}:objectViewer" ${MARKETING_BUCKET}
```

### Step 3.2: Grant Core Multi-Tenancy Permissions

First, grant the Dataproc VM service account the `serviceAccountTokenCreator` role on
the other two service accounts. This is the critical permission that allows the cluster
to impersonate the user-mapped service accounts.

```shell
gcloud iam service-accounts add-iam-policy-binding $FINANCE_SA \
    --member="serviceAccount:${DATAPROC_VM_SA}" \
    --role="roles/iam.serviceAccountTokenCreator"
gcloud iam service-accounts add-iam-policy-binding $MARKETING_SA \
    --member="serviceAccount:${DATAPROC_VM_SA}" \
    --role="roles/iam.serviceAccountTokenCreator"
```

Next, grant the `dataproc.worker` role to the Dataproc VM service account at the
project level.

```shell
gcloud projects add-iam-policy-binding $GOOGLE_PROJECT_ID \
    --member="serviceAccount:${DATAPROC_VM_SA}" \
    --role="roles/dataproc.worker"
```

### Step 3.3: Create the Secure Dataproc Cluster

Now, create the Dataproc cluster with the secure multi-tenancy user mapping. This flag
tells Dataproc which service account to use for jobs submitted by a specific user.

```shell
export CLUSTER_NAME="simple-secure-cluster"

gcloud dataproc clusters create $CLUSTER_NAME \
    --region=$REGION \
    --service-account=$DATAPROC_VM_SA \
    --image-version=2.2 \
    --scopes=https://www.googleapis.com/auth/iam,https://www.googleapis.com/auth/devstorage.full_control \
    --secure-multi-tenancy-user-mapping="${FINANCE_USER_EMAIL}=${FINANCE_SA},${MARKETING_USER_EMAIL}=${MARKETING_SA}"
```

### Step 3.4: Configure Staging and Temp Bucket Permissions

Dataproc automatically creates staging and temp buckets for its operations. We need to
grant the correct permissions on these buckets.

1. **Get Bucket Names:** First, retrieve the auto-generated bucket names.

   ```shell
   # It can take a moment for the cluster to report its bucket names.
   sleep 20
   export STAGING_BUCKET_URI="gs://$(gcloud dataproc clusters describe $CLUSTER_NAME --region=$REGION --format="value(config.configBucket)")"
   export TEMP_BUCKET_URI="gs://$(gcloud dataproc clusters describe $CLUSTER_NAME --region=$REGION --format="value(config.tempBucket)")"
   ```

2. **Grant User Permissions:** Grant the finance and marketing _users_ `objectAdmin` on
   the **staging bucket**. This allows them to submit jobs via `gcloud`.

   ```shell
   gsutil iam ch "user:${FINANCE_USER_EMAIL}:objectAdmin" "${STAGING_BUCKET_URI}"
   gsutil iam ch "user:${MARKETING_USER_EMAIL}:objectAdmin" "${STAGING_BUCKET_URI}"
   ```

3. **Grant Service Account Permissions:** Grant the finance and marketing _service
   accounts_ `objectAdmin` on the **temp bucket**. This allows them to write job logs
   and other temporary files.

   ```shell
   gsutil iam ch "serviceAccount:${FINANCE_SA}:objectAdmin" "${TEMP_BUCKET_URI}"
   gsutil iam ch "serviceAccount:${MARKETING_SA}:objectAdmin" "${TEMP_BUCKET_URI}"
   ```

---

## 4. Demo Execution Flow

**Important:** The following commands assume you are running them from the root of the
`dataproc-secure-multi-tenancy` directory.

Now you will test the setup by running jobs as each user.

### Step 4.1: Test as the Finance User

1. **Log in as the Finance User:**

   ```shell
   gcloud auth login ${FINANCE_USER_EMAIL}
   ```

2. **Run Tests:** Submit two PySpark jobs.
   - The first job reads from the finance bucket and is **expected to succeed**.
   - The second job reads from the marketing bucket and is **expected to fail**.

   ```shell
   # This test should SUCCEED
   gcloud dataproc jobs submit pyspark src/read_gcs_data.py \
       --cluster=$CLUSTER_NAME --region=$REGION \
       -- ${FINANCE_BUCKET}/finance.txt

   # This test should FAIL
   gcloud dataproc jobs submit pyspark src/read_gcs_data.py \
       --cluster=$CLUSTER_NAME --region=$REGION \
       -- ${MARKETING_BUCKET}/marketing.txt
   ```

### Step 4.2: Test as the Marketing User

1. **Log in as the Marketing User:**

   ```shell
   gcloud auth login ${MARKETING_USER_EMAIL}
   ```

2. **Run Tests:** Submit two PySpark jobs.
   - The first job reads from the marketing bucket and is **expected to succeed**.
   - The second job reads from the finance bucket and is **expected to fail**.

   ```shell
   # This test should SUCCEED
   gcloud dataproc jobs submit pyspark src/read_gcs_data.py \
       --cluster=$CLUSTER_NAME --region=$REGION \
       -- ${MARKETING_BUCKET}/marketing.txt

   # This test should FAIL
   gcloud dataproc jobs submit pyspark src/read_gcs_data.py \
       --cluster=$CLUSTER_NAME --region=$REGION \
       -- ${FINANCE_BUCKET}/finance.txt
   ```

---

## 5. Demo Teardown

To clean up the resources created during this demo, run the following commands.

1. **Delete the Dataproc Cluster:**

   ```shell
   gcloud dataproc clusters delete $CLUSTER_NAME --region=$REGION --quiet
   ```

2. **Delete the GCS Buckets and their contents:**

   ```shell
   gsutil rm -r ${FINANCE_BUCKET}
   gsutil rm -r ${MARKETING_BUCKET}
   # Note: The staging and temp buckets are deleted automatically with the cluster.
   ```

3. **Delete the Service Accounts:**

   ```shell
   gcloud iam service-accounts delete $FINANCE_SA --quiet
   gcloud iam service-accounts delete $MARKETING_SA --quiet
   gcloud iam service-accounts delete $DATAPROC_VM_SA --quiet
   ```
