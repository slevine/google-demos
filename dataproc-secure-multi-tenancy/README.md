# Dataproc Secure Multi-Tenancy Demo

This demo shows how to use Dataproc's Service Account-based Secure
Multi-tenancy feature to enforce fine-grained data access for different users on a
single, shared cluster. It provides a clear, practical example of how two distinct
users, each with different data access privileges, can run jobs on the same cluster
while being restricted to only the data they are authorized to see.

- **[Full Demo Guide](docs/dataproc-secure-multi-tenancy-demo.md)**

## Key Features Demonstrated

- **Shared Dataproc Cluster:** A single cluster serves multiple users, reducing
  operational overhead.
- **User-Level Data Isolation:** Securely enforce which user can access which GCS
  bucket.
- **Simplified IAM:** Achieves data separation without complex conditional IAM policies
  or deny rules.
- **Native Dataproc Security:** Uses the built-in `--secure-multi-tenancy-user-mapping`
  feature for robust, manageable security.

## Prerequisites

This project uses `uv` to manage its Python environment. Please see
the [full demo guide](docs/dataproc-secure-multi-tenancy-demo.md) for detailed setup
instructions.

## Useful Links

- [Dataproc Service Account-based Secure Multi-tenancy Documentation](https://cloud.google.com/dataproc/docs/concepts/iam/sa-multi-tenancy)
