"""
AWS Athena Service - Query S3 Data with SQL

Learning points:
- Athena is a serverless query service for S3 data
- Uses standard SQL (Presto engine)
- Pay per query (based on data scanned)
- Great for ad-hoc analytics on large datasets

Use cases in energy trading:
- Historical price analysis
- Trade pattern queries
- P&L aggregations across large datasets
- Audit and compliance reporting

IAM permissions required:
- athena:StartQueryExecution
- athena:GetQueryExecution
- athena:GetQueryResults
- s3:GetObject (for data)
- s3:PutObject (for results)
- glue:GetTable, glue:GetDatabase (for metadata)
"""
import boto3
from botocore.exceptions import ClientError
import time
import pandas as pd
from typing import Optional, Any
import logging

from config import get_settings

logger = logging.getLogger(__name__)


class AthenaService:
    """
    Service for querying S3 data using AWS Athena.

    Athena allows you to run SQL queries directly on data stored in S3
    without needing to load it into a database first.

    Architecture:
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Athena    │────▶│   S3 Data   │     │  S3 Results │
    │   Query     │     │   Bucket    │     │   Bucket    │
    └─────────────┘     └─────────────┘     └─────────────┘
          │                                        ▲
          │                                        │
          └────────────────────────────────────────┘
                    Query results stored
    """

    def __init__(self):
        settings = get_settings()

        # Initialize Athena client
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.athena_client = boto3.client(
                'athena',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        else:
            self.athena_client = boto3.client('athena', region_name=settings.aws_region)

        self.database = "pnl_demo_db"
        self.data_bucket = settings.s3_bucket_name
        self.results_bucket = f"{settings.s3_bucket_name}-athena-results"
        self.region = settings.aws_region

    def execute_query(
        self,
        query: str,
        timeout_seconds: int = 300
    ) -> Optional[pd.DataFrame]:
        """
        Execute an Athena query and return results as DataFrame.

        Steps:
        1. Start query execution
        2. Poll for completion
        3. Fetch and parse results

        Example:
            df = athena.execute_query("SELECT * FROM prices WHERE commodity = 'GAS'")
        """
        try:
            # Start query execution
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={
                    'OutputLocation': f's3://{self.results_bucket}/query-results/',
                    'EncryptionConfiguration': {'EncryptionOption': 'SSE_S3'}
                },
                WorkGroup='primary'
            )

            query_execution_id = response['QueryExecutionId']
            logger.info(f"Started Athena query: {query_execution_id}")

            # Wait for query to complete
            state = self._wait_for_query(query_execution_id, timeout_seconds)

            if state != 'SUCCEEDED':
                logger.error(f"Query failed with state: {state}")
                return None

            # Get results
            return self._get_query_results(query_execution_id)

        except ClientError as e:
            logger.error(f"Athena query failed: {e}")
            return None

    def _wait_for_query(
        self,
        query_execution_id: str,
        timeout_seconds: int
    ) -> str:
        """
        Poll Athena until query completes.

        States: QUEUED -> RUNNING -> SUCCEEDED/FAILED/CANCELLED
        """
        start_time = time.time()

        while True:
            response = self.athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            state = response['QueryExecution']['Status']['State']

            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                if state == 'FAILED':
                    reason = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                    logger.error(f"Query failed: {reason}")
                return state

            if time.time() - start_time > timeout_seconds:
                logger.error(f"Query timed out after {timeout_seconds}s")
                # Cancel the query
                self.athena_client.stop_query_execution(QueryExecutionId=query_execution_id)
                return 'TIMEOUT'

            time.sleep(1)  # Poll every second

    def _get_query_results(self, query_execution_id: str) -> pd.DataFrame:
        """
        Fetch query results and convert to DataFrame.
        """
        paginator = self.athena_client.get_paginator('get_query_results')
        results = []
        columns = []

        for page in paginator.paginate(QueryExecutionId=query_execution_id):
            # First row contains column headers
            if not columns:
                columns = [col['Name'] for col in page['ResultSet']['ResultSetMetadata']['ColumnInfo']]
                # Skip header row in first page
                rows = page['ResultSet']['Rows'][1:]
            else:
                rows = page['ResultSet']['Rows']

            for row in rows:
                values = [field.get('VarCharValue', None) for field in row['Data']]
                results.append(values)

        return pd.DataFrame(results, columns=columns)

    # ===================
    # Table Management
    # ===================

    def create_prices_table(self) -> bool:
        """
        Create Athena table for price data stored in S3.

        This creates an EXTERNAL table - data stays in S3,
        Athena just knows how to query it.
        """
        query = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database}.prices (
            price_date DATE,
            commodity STRING,
            delivery_period STRING,
            price DOUBLE,
            currency STRING,
            price_type STRING,
            source STRING
        )
        PARTITIONED BY (year INT, month INT)
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{self.data_bucket}/prices/'
        TBLPROPERTIES ('skip.header.line.count'='1')
        """

        try:
            self.execute_query(query)
            logger.info("Created prices table")
            return True
        except Exception as e:
            logger.error(f"Failed to create prices table: {e}")
            return False

    def create_trades_table(self) -> bool:
        """
        Create Athena table for archived trade data.
        """
        query = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database}.trades (
            trade_id STRING,
            contract_id INT,
            direction STRING,
            quantity DOUBLE,
            price DOUBLE,
            trade_date TIMESTAMP,
            delivery_date TIMESTAMP,
            status STRING,
            trader STRING
        )
        PARTITIONED BY (year INT, month INT)
        ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
        LOCATION 's3://{self.data_bucket}/archives/trades/'
        """

        try:
            self.execute_query(query)
            logger.info("Created trades table")
            return True
        except Exception as e:
            logger.error(f"Failed to create trades table: {e}")
            return False

    def create_database(self) -> bool:
        """
        Create the Athena database if it doesn't exist.
        """
        query = f"CREATE DATABASE IF NOT EXISTS {self.database}"
        try:
            # For CREATE DATABASE, we need to use a default database
            response = self.athena_client.start_query_execution(
                QueryString=query,
                ResultConfiguration={
                    'OutputLocation': f's3://{self.results_bucket}/query-results/'
                }
            )
            self._wait_for_query(response['QueryExecutionId'], 60)
            logger.info(f"Created database: {self.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False

    def refresh_partitions(self, table_name: str) -> bool:
        """
        Refresh table partitions to discover new data.

        When new data is added to S3, Athena needs to know about
        new partitions. MSCK REPAIR TABLE scans for new partitions.
        """
        query = f"MSCK REPAIR TABLE {self.database}.{table_name}"
        try:
            self.execute_query(query)
            logger.info(f"Refreshed partitions for {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh partitions: {e}")
            return False

    # ===================
    # Pre-built Queries
    # ===================

    def get_price_history(
        self,
        commodity: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Get historical prices for a commodity.

        Example:
            df = athena.get_price_history('GAS', '2024-01-01', '2024-12-31')
        """
        query = f"""
        SELECT
            price_date,
            commodity,
            delivery_period,
            price,
            currency,
            source
        FROM {self.database}.prices
        WHERE commodity = '{commodity}'
          AND price_date BETWEEN DATE '{start_date}' AND DATE '{end_date}'
        ORDER BY price_date
        """
        return self.execute_query(query)

    def get_price_statistics(
        self,
        commodity: str,
        year: int
    ) -> Optional[pd.DataFrame]:
        """
        Get price statistics (min, max, avg, volatility) for a commodity.

        This demonstrates Athena's aggregation capabilities.
        """
        query = f"""
        SELECT
            commodity,
            year,
            COUNT(*) as data_points,
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            STDDEV(price) as price_volatility,
            APPROX_PERCENTILE(price, 0.5) as median_price
        FROM {self.database}.prices
        WHERE commodity = '{commodity}'
          AND year = {year}
        GROUP BY commodity, year
        """
        return self.execute_query(query)

    def get_trade_summary(
        self,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Get trade summary aggregations.
        """
        query = f"""
        SELECT
            direction,
            COUNT(*) as trade_count,
            SUM(quantity) as total_volume,
            AVG(price) as avg_price,
            SUM(quantity * price) as total_notional
        FROM {self.database}.trades
        WHERE trade_date BETWEEN TIMESTAMP '{start_date}' AND TIMESTAMP '{end_date}'
        GROUP BY direction
        """
        return self.execute_query(query)

    def get_daily_pnl_analysis(
        self,
        commodity: str,
        year: int,
        month: int
    ) -> Optional[pd.DataFrame]:
        """
        Analyze daily P&L patterns using price data.

        Calculates daily returns and identifies significant moves.
        """
        query = f"""
        WITH daily_prices AS (
            SELECT
                price_date,
                price,
                LAG(price) OVER (ORDER BY price_date) as prev_price
            FROM {self.database}.prices
            WHERE commodity = '{commodity}'
              AND year = {year}
              AND month = {month}
        )
        SELECT
            price_date,
            price,
            prev_price,
            (price - prev_price) as price_change,
            ((price - prev_price) / prev_price * 100) as pct_change
        FROM daily_prices
        WHERE prev_price IS NOT NULL
        ORDER BY price_date
        """
        return self.execute_query(query)

    def get_query_cost_estimate(self, query: str) -> dict:
        """
        Estimate the cost of running a query.

        Athena charges ~$5 per TB of data scanned.
        """
        try:
            # Use EXPLAIN to get execution plan without running
            explain_query = f"EXPLAIN {query}"
            response = self.athena_client.start_query_execution(
                QueryString=explain_query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={
                    'OutputLocation': f's3://{self.results_bucket}/query-results/'
                }
            )

            self._wait_for_query(response['QueryExecutionId'], 60)

            # Get statistics
            execution = self.athena_client.get_query_execution(
                QueryExecutionId=response['QueryExecutionId']
            )

            stats = execution['QueryExecution'].get('Statistics', {})
            data_scanned = stats.get('DataScannedInBytes', 0)

            # Athena pricing: ~$5 per TB
            cost_per_tb = 5.0
            estimated_cost = (data_scanned / (1024**4)) * cost_per_tb

            return {
                'data_scanned_bytes': data_scanned,
                'data_scanned_mb': round(data_scanned / (1024**2), 2),
                'estimated_cost_usd': round(estimated_cost, 6)
            }

        except Exception as e:
            logger.error(f"Failed to estimate query cost: {e}")
            return {'error': str(e)}


# Singleton instance
_athena_service: Optional[AthenaService] = None


def get_athena_service() -> AthenaService:
    """Get Athena service singleton."""
    global _athena_service
    if _athena_service is None:
        _athena_service = AthenaService()
    return _athena_service
