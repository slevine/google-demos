"""
This module provides a TradeGenerator class to create and insert mock trade data into BigQuery.

It is designed for interactive use in environments like iPython or Jupyter notebooks
to demonstrate interactions with BigQuery, including handling different schemas
and generating data in batches.

Configuration is handled via environment variables:
- GOOGLE_PROJECT_ID: Your Google Cloud project ID.
- BQ_TRADES_DATASET_ID: The BigQuery dataset ID for trades.
"""

import logging
import os
import random
import uuid
from datetime import datetime, timezone, time, timedelta
from typing import List, Dict, Optional, Any

import pytz
from google.cloud import bigquery
from .trade_data import tickers, cat_handling_codes, cat_event_types

logger = logging.getLogger(__name__)


class TradeGenerator:
    """
    A class to generate and insert trade data into a BigQuery table.

    Attributes:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.
        client (bigquery.Client): The BigQuery client instance.
        table_ref_full (str): The fully qualified BigQuery table reference.
    """

    _DEFAULT_TABLE_NAME = "trades"

    def __init__(self) -> None:
        """
        Initializes the BigQuery client and sets up configuration from environment variables.

        Raises:
            RuntimeError: If required environment variables are not set.
        """
        try:
            self.project_id = os.environ["GOOGLE_PROJECT_ID"]
            self.dataset_id = os.environ["BQ_TRADES_DATASET_ID"]
        except KeyError as e:
            logger.error("Missing required environment variable: %s", e)
            raise RuntimeError(
                f"Configuration error: Please set the {e} environment variable."
            ) from e

        self.client = bigquery.Client(project=self.project_id)
        self._active_table_name = self._DEFAULT_TABLE_NAME
        self.table_ref_full = ""  # Will be set by set_active_table
        self.set_active_table(self._DEFAULT_TABLE_NAME)
        logger.info(
            "TradeGenerator initialized for project '%s' and dataset '%s'",
            self.project_id,
            self.dataset_id,
        )

    def set_active_table(self, new_table_name: str) -> None:
        """
        Sets the active BigQuery table for data insertion.

        Args:
            new_table_name: The name of the target table (e.g., 'trades_v1').
        """
        if not new_table_name:
            logger.warning(
                (
                    "Invalid table name provided: '%s'. Must be a non-empty string."
                    "Keeping current table: '%s'."
                ),
                new_table_name,
                self._active_table_name,
            )
            return

        self._active_table_name = new_table_name
        self.table_ref_full = (
            f"{self.project_id}.{self.dataset_id}.{self._active_table_name}"
        )
        logger.info("Active BigQuery table set to: %s", self.table_ref_full)

    @staticmethod
    def _create_base_trade() -> Dict[str, Any]:
        """Creates a dictionary representing a single base trade."""
        return {
            "trade_id": str(uuid.uuid4()),
            "ticker": random.choice(tickers),
            "price": round(random.uniform(150.0, 3000.0), 2),
            "quantity": random.randint(10, 5000),
            "trade_side": random.choice(["BUY", "SELL"]),
            "executing_account": f"ACC-TRD-{random.randint(1, 5):02d}",
        }

    def _insert_trades_via_streaming_api(self, trades: List[Dict[str, any]]) -> None:
        """
        Inserts a list of trade records into the active BigQuery table using the Storage Write API.

        Args:
            trades: A list of dictionaries, where each represents a trade.
        """
        if not trades:
            logger.info("No trades to insert.")
            return

        try:
            table = self.client.get_table(self.table_ref_full)
            errors = self.client.insert_rows_json(table, trades)
            if not errors:
                buys = sum(1 for t in trades if t["trade_side"] == "BUY")
                sells = len(trades) - buys
                last_tickers = ", ".join(
                    [t["ticker"] for t in trades[-3:]]
                )  # Get last 3 tickers
                logger.info(
                    "Successfully added %d trades (BUYS: %d, SELLS: %d) into %s. Last tickers: %s",
                    len(trades),
                    buys,
                    sells,
                    self._active_table_name,
                    last_tickers,
                )
            else:
                logger.error(
                    "Encountered errors while streaming rows to %s: %s",
                    self._active_table_name,
                    errors,
                )
        except Exception as e:
            logger.error(
                "Failed to stream batch into %s: %s",
                self._active_table_name,
                e,
                exc_info=True,
            )

    def _insert_trades_via_dml(self, trades: List[Dict[str, any]]) -> None:
        """
        Inserts a list of trade records into the active BigQuery table using a DML INSERT statement.

        NOTE FOR REVIEWERS:
        While the BigQuery streaming API (`insert_rows_json`) is typically preferred
        for ingestion, it writes to a buffer that can have a delay (from minutes to
        hours) before the data is available in the base table and flushed to GCS.

        For this interactive demo, immediate read-after-write consistency is critical
        to show changes being reflected in Spark right away. Therefore, a synchronous
        DML INSERT is used to bypass the streaming buffer and guarantee that the
        data is immediately queryable.
        """
        if not trades:
            logger.info("No trades to insert.")
            return

        columns = list(trades[0].keys())
        col_string = ", ".join(f"`{c}`" for c in columns)

        def format_value(value):
            if isinstance(value, str):
                if "+00:00" in value and "T" in value:
                    return f"TIMESTAMP('{value}')"
                return f"'{value.replace("'", "''")}'"
            if isinstance(value, dict):  # For STRUCT
                struct_vals = []
                for k, v in value.items():
                    struct_vals.append(f"{format_value(v)} AS `{k}`")
                return f"STRUCT({', '.join(struct_vals)})"
            if value is None:
                return "NULL"
            return str(value)

        values_list = []
        for trade in trades:
            value_str = (
                f"({', '.join([format_value(trade.get(col)) for col in columns])})"
            )
            values_list.append(value_str)

        values_string = ",\n".join(values_list)
        query = (
            f"INSERT INTO `{self.table_ref_full}` ({col_string}) VALUES {values_string}"
        )

        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for the job to complete
            buys = sum(1 for t in trades if t.get("trade_side") == "BUY")
            sells = len(trades) - buys
            last_tickers = ", ".join(
                [t["ticker"] for t in reversed(trades[:3])]
            )  # Get last 3 tickers
            logger.info(
                "Successfully added %d trades (BUYS: %d, SELLS: %d) into %s. Last tickers: %s",
                len(trades),
                buys,
                sells,
                self._active_table_name,
                last_tickers,
            )
        except Exception as e:
            logger.error(
                "Failed to insert batch via DML into %s: %s",
                self._active_table_name,
                e,
                exc_info=True,
            )

    def _generate_deterministic_trades(self, count: int) -> None:
        """Generates trades with the current UTC timestamp."""
        logger.info(
            "Generating %d deterministic trade(s) for table %s using current timestamp...",
            count,
            self._active_table_name,
        )
        trades = []
        for _ in range(count):
            trade = self._create_base_trade()
            trade["trade_timestamp"] = datetime.now(timezone.utc).isoformat()
            trades.append(trade)
        self._insert_trades_via_dml(trades)

    def _create_realistic_trades_list(self, count: int) -> List[Dict[str, any]]:
        """Creates a list of trades with realistic, randomized timestamps within market hours."""
        eastern_tz = pytz.timezone("America/New_York")
        now_edt = datetime.now(eastern_tz)
        today_edt = now_edt.date()

        market_open_edt = eastern_tz.localize(datetime.combine(today_edt, time(9, 30)))
        market_close_edt = eastern_tz.localize(datetime.combine(today_edt, time(16, 0)))

        if now_edt < market_open_edt:
            logger.info(
                "Pre-market hours detected. Generating trades for the previous trading day."
            )
            trade_date = today_edt - timedelta(days=1)
            if trade_date.weekday() >= 5:  # Saturday or Sunday
                trade_date -= timedelta(
                    days=trade_date.weekday() - 4
                )  # Go back to Friday
            start_time_for_generation = eastern_tz.localize(
                datetime.combine(trade_date, time(9, 30))
            )
            end_time_for_generation = eastern_tz.localize(
                datetime.combine(trade_date, time(16, 0))
            )
        else:
            start_time_for_generation = market_open_edt
            end_time_for_generation = min(now_edt, market_close_edt)

        start_ts = int(start_time_for_generation.timestamp())
        end_ts = int(end_time_for_generation.timestamp())

        logger.info(
            "Generating %d realistic trades for table %s between %s and %s EDT...",
            count,
            self._active_table_name,
            start_time_for_generation.strftime("%Y-%m-%d %H:%M:%S"),
            end_time_for_generation.strftime("%Y-%m-%d %H:%M:%S"),
        )

        trades = []
        for _ in range(count):
            random_ts_epoch = random.randint(start_ts, end_ts)
            trade = self._create_base_trade()
            trade["trade_timestamp"] = datetime.fromtimestamp(
                random_ts_epoch, tz=timezone.utc
            ).isoformat()
            trades.append(trade)
        return trades

    def _generate_realistic_trades(self, count: int) -> None:
        """Generates and inserts trades with realistic, randomized timestamps within market hours."""
        trades = self._create_realistic_trades_list(count)
        self._insert_trades_via_dml(trades)

    def generate_trades(
        self, count: Optional[int] = None, realistic_timestamps: bool = True
    ) -> None:
        """
        Main public method to generate trades.

        Args:
            count: Number of trades to generate. Defaults to a random number between 5 and 12.
            realistic_timestamps: If True (default), generates trades with realistic
                                  market-hour timestamps. If False, generates trades with the
                                  current timestamp.
        """
        if count is None:
            count = random.randint(5, 12)

        if realistic_timestamps:
            self._generate_realistic_trades(count)
        else:
            self._generate_deterministic_trades(count)

    def generate_updated_trades(self, count: Optional[int] = None) -> None:
        """
        Generates trades that include the nested 'cat_compliance' struct.

        Args:
            count: Number of trades to generate. Defaults to a random number between 5 and 12.
        """
        if count is None:
            count = random.randint(5, 12)

        logger.info(
            "Generating %d trades with expanded CAT compliance data for table %s...",
            count,
            self._active_table_name,
        )

        trades = []
        for _ in range(count):
            trade = self._create_base_trade()
            trade["trade_timestamp"] = datetime.now(timezone.utc).isoformat()
            trade["cat_compliance"] = {
                "reporter_id": f"CAT_DESK_{random.randint(1, 4):02d}",
                "order_event_type": random.choice(cat_event_types),
                "handling_instructions": random.choice(cat_handling_codes),
                "session_id": f"SESS-{uuid.uuid4()}",
                "reported_timestamp": datetime.now(timezone.utc).isoformat(),
            }
            trades.append(trade)
        self._insert_trades_via_dml(trades)

    def generate_trades_in_batches(
        self, total_trades: int, batch_size: int = 1000
    ) -> None:
        """
        Generates a large volume of trades and inserts them using the streaming API.

        Args:
            total_trades: The total number of trades to create.
            batch_size: The number of trades to generate in a single batch.
        """
        logger.info(
            "Starting generation of %d trades for table %s, in batches of up to %d.",
            total_trades,
            self._active_table_name,
            batch_size,
        )
        num_batches = (total_trades + batch_size - 1) // batch_size
        for i in range(num_batches):
            current_batch_size = min(batch_size, total_trades - (i * batch_size))
            if current_batch_size <= 0:
                break
            logger.info(
                "Processing batch %d of %d (size: %d)...",
                i + 1,
                num_batches,
                current_batch_size,
            )
            # Using realistic timestamps for large batches is more representative
            trades = self._create_realistic_trades_list(count=current_batch_size)
            self._insert_trades_via_streaming_api(trades)

        logger.info(
            "Finished generating %d trades in %d batches.", total_trades, num_batches
        )
