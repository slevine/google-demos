import sys
from pyspark.sql import SparkSession

def main():
    """
    Reads and displays a text file from a GCS path.
    """
    if len(sys.argv) != 2:
        print("Usage: read_gcs_data.py <gcs_path>")
        sys.exit(1)

    gcs_path = sys.argv[1]
    app_name = f"ReadDataFrom-{gcs_path.split('/')[-2]}"

    try:
        spark = SparkSession.builder.appName(app_name).getOrCreate()
        print(f"Attempting to read from: {gcs_path}")
        df = spark.read.text(gcs_path)
        df.show(truncate=False)
        print(f"Successfully read from: {gcs_path}")
    except Exception as e:
        print(f"ERROR: Failed to read from {gcs_path}")
        print(e)
        # Exit with a non-zero status code to indicate failure,
        # which is important for automated scripts.
        sys.exit(1)

if __name__ == "__main__":
    main()