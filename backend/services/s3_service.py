"""
AWS S3 Service - Market Data Storage

Learning points:
- boto3 for AWS SDK
- S3 bucket operations
- Handling CSV and JSON data
- Error handling for cloud services
- IAM permissions required:
  - s3:GetObject
  - s3:PutObject
  - s3:ListBucket
  - s3:DeleteObject
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
import json
import io
from datetime import date, datetime
from typing import Optional
import logging

from config import get_settings

logger = logging.getLogger(__name__)


class S3Service:
    """
    Service for interacting with AWS S3 for market data storage.

    Use cases:
    - Store historical price data
    - Archive trade data
    - Store large datasets for analysis
    - Share data between services
    """

    def __init__(self):
        settings = get_settings()

        # Initialize S3 client
        # If running on AWS (EC2, ECS, Lambda), use IAM roles instead of keys
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        else:
            # Use default credentials chain (IAM role, env vars, ~/.aws/credentials)
            self.s3_client = boto3.client('s3', region_name=settings.aws_region)

        self.bucket_name = settings.s3_bucket_name
        self.region = settings.aws_region

    def _check_bucket_exists(self) -> bool:
        """Check if the configured bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                logger.warning(f"Bucket {self.bucket_name} does not exist")
                return False
            raise

    def create_bucket_if_not_exists(self) -> bool:
        """
        Create the S3 bucket if it doesn't exist.

        Note: In production, buckets should be created via Terraform, not code.
        """
        try:
            if self._check_bucket_exists():
                return True

            # Create bucket (region-specific configuration)
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            logger.info(f"Created bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            return False

    # ===================
    # Market Price Operations
    # ===================

    def upload_price_data(
        self,
        commodity: str,
        price_date: date,
        data: pd.DataFrame
    ) -> bool:
        """
        Upload price data to S3.

        Stores as: prices/{commodity}/{year}/{month}/{date}.csv

        Example:
            prices/GAS/2024/12/2024-12-03.csv
        """
        try:
            # Construct S3 key (path)
            key = f"prices/{commodity}/{price_date.year}/{price_date.month:02d}/{price_date.isoformat()}.csv"

            # Convert DataFrame to CSV
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv',
                Metadata={
                    'commodity': commodity,
                    'date': price_date.isoformat(),
                    'row_count': str(len(data))
                }
            )

            logger.info(f"Uploaded price data to s3://{self.bucket_name}/{key}")
            return True

        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to upload price data: {e}")
            return False

    def get_price_data(
        self,
        commodity: str,
        price_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve price data from S3.
        """
        try:
            key = f"prices/{commodity}/{price_date.year}/{price_date.month:02d}/{price_date.isoformat()}.csv"

            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            # Read CSV from response body
            csv_content = response['Body'].read().decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))

            logger.info(f"Retrieved price data from s3://{self.bucket_name}/{key}")
            return df

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.debug(f"No price data found for {commodity} on {price_date}")
                return None
            logger.error(f"Failed to get price data: {e}")
            return None

    def list_price_files(
        self,
        commodity: str,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> list[str]:
        """
        List available price data files.
        """
        try:
            prefix = f"prices/{commodity}/"
            if year:
                prefix += f"{year}/"
                if month:
                    prefix += f"{month:02d}/"

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            files = []
            for obj in response.get('Contents', []):
                files.append(obj['Key'])

            return files

        except ClientError as e:
            logger.error(f"Failed to list price files: {e}")
            return []

    # ===================
    # Trade Archive Operations
    # ===================

    def archive_trades(
        self,
        trades_data: list[dict],
        archive_date: date
    ) -> bool:
        """
        Archive trade data to S3.

        Stores as: archives/trades/{year}/{month}/trades_{date}.json
        """
        try:
            key = f"archives/trades/{archive_date.year}/{archive_date.month:02d}/trades_{archive_date.isoformat()}.json"

            # Convert to JSON
            json_data = json.dumps(trades_data, default=str, indent=2)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json',
                Metadata={
                    'archive_date': archive_date.isoformat(),
                    'trade_count': str(len(trades_data))
                }
            )

            logger.info(f"Archived {len(trades_data)} trades to s3://{self.bucket_name}/{key}")
            return True

        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to archive trades: {e}")
            return False

    def get_archived_trades(self, archive_date: date) -> Optional[list[dict]]:
        """
        Retrieve archived trade data.
        """
        try:
            key = f"archives/trades/{archive_date.year}/{archive_date.month:02d}/trades_{archive_date.isoformat()}.json"

            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            json_content = response['Body'].read().decode('utf-8')
            return json.loads(json_content)

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                return None
            logger.error(f"Failed to get archived trades: {e}")
            return None

    # ===================
    # Bulk Data Operations
    # ===================

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        key: str,
        file_format: str = 'csv'
    ) -> bool:
        """
        Upload a pandas DataFrame to S3.

        Args:
            df: DataFrame to upload
            key: S3 object key (path)
            file_format: 'csv' or 'parquet'
        """
        try:
            if file_format == 'parquet':
                buffer = io.BytesIO()
                df.to_parquet(buffer, index=False)
                content_type = 'application/octet-stream'
                body = buffer.getvalue()
            else:  # CSV
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                content_type = 'text/csv'
                body = buffer.getvalue()

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType=content_type
            )

            logger.info(f"Uploaded DataFrame to s3://{self.bucket_name}/{key}")
            return True

        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to upload DataFrame: {e}")
            return False

    def download_dataframe(
        self,
        key: str,
        file_format: str = 'csv'
    ) -> Optional[pd.DataFrame]:
        """
        Download a DataFrame from S3.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            if file_format == 'parquet':
                buffer = io.BytesIO(response['Body'].read())
                return pd.read_parquet(buffer)
            else:  # CSV
                content = response['Body'].read().decode('utf-8')
                return pd.read_csv(io.StringIO(content))

        except ClientError as e:
            logger.error(f"Failed to download DataFrame: {e}")
            return None

    # ===================
    # Utility Methods
    # ===================

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary access.

        Useful for:
        - Sharing data with external parties
        - Downloading large files through frontend
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def delete_object(self, key: str) -> bool:
        """Delete an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object: {e}")
            return False


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get S3 service singleton."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
