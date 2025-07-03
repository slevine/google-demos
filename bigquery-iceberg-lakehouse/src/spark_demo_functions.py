"""
This module provides a SparkDemo class for interacting with an Iceberg data lakehouse
stored on Google Cloud Storage.

It is designed for interactive use in environments like iPython or Jupyter notebooks
to demonstrate Spark and Iceberg capabilities.

Configuration is handled via environment variables:
- GCS_WAREHOUSE_PATH: The GCS path to the Iceberg warehouse (e.g., 'gs://your-bucket/warehouse/').
"""

import logging
import os
from datetime import datetime
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.functions import desc, max
from tabulate import tabulate

logger = logging.getLogger(__name__)

ICEBERG_SPARK_RUNTIME_JAR = "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.1"
GCS_CONNECTOR_JAR = "https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop3-2.2.20/gcs-connector-hadoop3-2.2.20-shaded.jar"


class SparkDemo:
    """
    A class to manage a Spark session and interact with an Iceberg data lakehouse.

    Attributes:
        warehouse_path (str): The GCS path to the Iceberg warehouse.
        spark (SparkSession): The active SparkSession instance.
        catalog_table_name (str): The fully qualified name of the active Iceberg table in the Spark catalog.
    """

    _DEFAULT_TABLE_NAME = "trades"

    def __init__(self, warehouse_path: Optional[str] = None) -> None:
        """
        Initializes the Spark session and sets up configuration.

        Args:
            warehouse_path: The GCS path to the Iceberg warehouse. If not provided,
                            it's read from the GCS_WAREHOUSE_PATH environment variable.
        Raises:
            ValueError: If the warehouse path is not provided or found in the environment.
        """
        self.warehouse_path = warehouse_path or os.environ.get("GCS_WAREHOUSE_PATH")
        if not self.warehouse_path:
            raise ValueError(
                "GCS warehouse path must be provided either as an argument "
                "or via the GCS_WAREHOUSE_PATH environment variable."
            )

        self.spark = self._initialize_spark()
        self._active_table_name = self._DEFAULT_TABLE_NAME
        self.catalog_table_name = ""  # Will be set by set_active_table
        self.set_active_table(self._DEFAULT_TABLE_NAME)
        logger.info("SparkDemo initialized. Warehouse is at '%s'", self.warehouse_path)

    def _initialize_spark(self) -> SparkSession:
        """Builds and configures the SparkSession for Iceberg and GCS."""
        logger.info("Initializing Spark session with Iceberg and GCS support...")

        builder = (
            SparkSession.builder.appName("IcebergLakehouseDemo")
            .config("spark.jars.packages", ICEBERG_SPARK_RUNTIME_JAR)
            .config("spark.jars", GCS_CONNECTOR_JAR)
            .config(
                "spark.hadoop.fs.gs.impl",
                "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem",
            )
            .config("spark.hadoop.google.cloud.auth.implicit.enabled", "true")
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.iceberg.spark.SparkSessionCatalog",
            )
            .config("spark.sql.catalog.spark_catalog.type", "hadoop")
            .config("spark.sql.catalog.spark_catalog.warehouse", self.warehouse_path)
        )

        # --- Environment-Aware Authentication ---
        adc_path = os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        )
        if os.path.exists(adc_path):
            logger.info("Found local ADC file. Configuring Spark to use: %s", adc_path)
            builder = builder.config(
                "spark.hadoop.google.cloud.auth.service.account.json.keyfile", adc_path
            )
        else:
            logger.info(
                "No local ADC file found. Assuming VM or other cloud environment with implicit credentials."
            )

        return builder.getOrCreate()

    def set_active_table(self, new_table_name: str) -> None:
        """
        Sets the active Iceberg table for subsequent operations.

        Args:
            new_table_name: The name of the target table (e.g., 'trades_v1').
        """
        if not isinstance(new_table_name, str) or not new_table_name:
            logger.warning(
                "Invalid table name: '%s'. Must be a non-empty string. Keeping current: '%s'.",
                new_table_name,
                self._active_table_name,
            )
            return
        self._active_table_name = new_table_name
        self.catalog_table_name = f"spark_catalog.{self._active_table_name}"
        logger.info("Active Spark table set to: %s", self.catalog_table_name)

    @staticmethod
    def _show_df(df: DataFrame, n: int = 10) -> None:
        """Displays a Spark DataFrame in a nicely formatted table using tabulate."""
        try:
            pandas_df = df.limit(n).toPandas()
            print(tabulate(pandas_df, headers="keys", tablefmt="psql", showindex=False))
        except Exception as e:
            logger.warning(
                "Tabulate formatting failed, falling back to default Spark show(). Error: %s",
                e,
            )
            df.show(n, truncate=False)

    def latest(self, n: int = 10) -> None:
        """
        Shows the latest N trades from the active Iceberg table.

        Args:
            n: The number of trades to display.
        """
        logger.info("Querying latest %d trades from %s...", n, self.catalog_table_name)
        try:
            df = self.spark.table(self.catalog_table_name)
            latest_trades = df.orderBy(desc("trade_timestamp"))
            self._show_df(latest_trades, n)
            logger.info(
                "Latest %d trades fetched at %s", n, datetime.now().strftime("%H:%M:%S")
            )
        except Exception as e:
            logger.error(
                "Error reading table %s: %s", self.catalog_table_name, e, exc_info=True
            )

    def schema(self) -> None:
        """Shows the schema of the active Iceberg table."""
        logger.info("Fetching schema for %s...", self.catalog_table_name)
        try:
            df = self.spark.table(self.catalog_table_name)
            df.printSchema()
        except Exception as e:
            logger.error(
                "Error reading schema for %s: %s",
                self.catalog_table_name,
                e,
                exc_info=True,
            )

    def count(self) -> int:
        """Returns the total row count in the active table."""
        logger.info("Counting total trades in %s...", self.catalog_table_name)
        try:
            df = self.spark.table(self.catalog_table_name)
            total = df.count()
            logger.info("Total trades: %s", f"{total:,}")
            return total
        except Exception as e:
            logger.error(
                "Error counting rows in %s: %s",
                self.catalog_table_name,
                e,
                exc_info=True,
            )
            return 0

    def status(self) -> None:
        """Shows a quick summary of the active table."""
        logger.info("Fetching status for %s...", self.catalog_table_name)
        try:
            df = self.spark.table(self.catalog_table_name)
            total = df.count()
            latest_ts_row = df.agg(max("trade_timestamp")).collect()
            latest_timestamp = latest_ts_row[0][0] if latest_ts_row else None
            unique_tickers = df.select("ticker").distinct().count()

            status_data = [
                ("Total Trades", f"{total:,}"),
                ("Active Tickers", unique_tickers),
                (
                    "Latest Trade",
                    latest_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if latest_timestamp
                    else "N/A",
                ),
            ]
            print(
                "\n"
                + tabulate(status_data, headers=("Metric", "Value"), tablefmt="psql")
                + "\n"
            )
        except Exception as e:
            logger.error(
                "Error getting status for %s: %s",
                self.catalog_table_name,
                e,
                exc_info=True,
            )

    def list_snapshots(self) -> None:
        """Lists all valid, queryable snapshots from the table's history."""
        logger.info("Reading table history for %s...", self.catalog_table_name)
        try:
            history_df = self.spark.sql(
                f"SELECT * FROM {self.catalog_table_name}.history"
            )
            history_df.orderBy("made_current_at").show(truncate=False)
            logger.info("Any snapshot ID from this list is valid for time travel.")
        except Exception as e:
            logger.error(
                "Error reading table history for %s: %s",
                self.catalog_table_name,
                e,
                exc_info=True,
            )

    def show_trades_at_snapshot(self, snapshot_id: str, n: int = 20) -> None:
        """
        Performs a time-travel query to a specific snapshot ID.

        Args:
            snapshot_id: The snapshot ID to query.
            n: The number of rows to display.
        """
        logger.info("Time traveling to snapshot ID: %s", snapshot_id)
        try:
            df_historical = self.spark.read.option(
                "snapshot-id", str(snapshot_id)
            ).table(self.catalog_table_name)
            logger.info("Schema as of snapshot %s:", snapshot_id)
            df_historical.printSchema()
            logger.info("Top %d most recent trades at that point in time:", n)
            self._show_df(df_historical.orderBy(desc("trade_timestamp")), n)
        except Exception as e:
            logger.error(
                "Error during time travel to snapshot %s: %s",
                snapshot_id,
                e,
                exc_info=True,
            )

    def show_ml_code(self, filepath: str = "src/spark_ml.py") -> None:
        """
        Displays code from a file with syntax highlighting.

        Args:
            filepath: The path to the Python file to display.
        """
        logger.info("Displaying code from '%s'...", filepath)
        try:
            from pygments import highlight
            from pygments.lexers import PythonLexer
            from pygments.formatters import TerminalFormatter

            with open(filepath, "r") as f:
                code = f.read()

            # Dynamically insert the current table name into the code for display
            code = code.replace(
                'table("spark_catalog.trades")', f'table("{self.catalog_table_name}")'
            )
            print("\n" + "-" * 80)
            print(
                f"--- Code from: {filepath} (dynamically updated for table: {self.catalog_table_name}) ---"
            )
            print(highlight(code, PythonLexer(), TerminalFormatter()))
            print("-" * 80 + "\n")

        except ImportError:
            logger.warning(
                "Pygments not found. Please `pip install Pygments` for syntax highlighting."
            )
            self.show_ml_code_fallback(filepath)
        except FileNotFoundError:
            logger.error("File not found at '%s'", filepath)
        except Exception as e:
            logger.error("An unexpected error occurred while displaying code: %s", e)

    def show_ml_code_fallback(self, filepath: str) -> None:
        """Plain text fallback for displaying code if Pygments fails."""
        try:
            with open(filepath, "r") as f:
                code = f.read().replace(
                    'table("spark_catalog.trades")',
                    f'table("{self.catalog_table_name}")',
                )
                print(code)
        except FileNotFoundError:
            logger.error("File not found at '%s'", filepath)

    def stop(self) -> None:
        """Stops the active Spark session."""
        logger.info("Stopping Spark session.")
        self.spark.stop()
