"""
Application Configuration using Pydantic Settings.

Learning points:
- Environment variable management
- Pydantic Settings for validation
- Different configs for dev/prod
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in .env file or system environment.
    """

    # Application
    app_name: str = "PnL Demo API"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./pnl_demo.db"

    # For PostgreSQL, use:
    # database_url: str = "postgresql://user:password@localhost:5432/pnl_demo"

    # PostgreSQL specific (if not using DATABASE_URL)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None

    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "eu-west-1"
    s3_bucket_name: str = "pnl-demo-market-data"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """
        Construct database URL from components if DATABASE_URL not set.
        """
        if self.database_url and not self.database_url.startswith("sqlite"):
            return self.database_url

        if all([self.postgres_host, self.postgres_user, self.postgres_password, self.postgres_db]):
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

        return self.database_url

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are only loaded once.
    """
    return Settings()


# Example .env file content
ENV_EXAMPLE = """
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database (PostgreSQL)
DATABASE_URL=postgresql://pnl_user:pnl_password@localhost:5432/pnl_demo

# Or use separate components:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=pnl_user
# POSTGRES_PASSWORD=pnl_password
# POSTGRES_DB=pnl_demo

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=eu-west-1
S3_BUCKET_NAME=pnl-demo-market-data

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
"""
