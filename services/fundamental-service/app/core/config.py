from pathlib import Path

from pydantic import Field
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).parent.parent.parent.parent.parent / ".env"


class Config(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = Field(default="fundamental-analysis-service", validation_alias="APP_NAME")
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")

    # PostgreSQL (analysis_db)
    POSTGRES_USER: str = Field(validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: SecretStr = Field(validation_alias="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(validation_alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(validation_alias="POSTGRES_PORT")
    POSTGRES_DB_NAME: str = Field(validation_alias="POSTGRES_ANALYSIS_DB")

    # Redis
    REDIS_PASSWORD: SecretStr = Field(validation_alias="REDIS_PASSWORD")
    REDIS_HOST: str = Field(validation_alias="REDIS_HOST")
    REDIS_PORT: str = Field(validation_alias="REDIS_PORT")
    REDIS_DB: str = Field(validation_alias="REDIS_TECH_DB")

    # Redis TTL
    VALUATION_CACHE_TTL: int = Field(default=3600, validation_alias="VALUATION_CACHE_TTL")
    METRICS_CACHE_TTL: int = Field(default=1800, validation_alias="METRICS_CACHE_TTL")

    # RabbitMQ
    RABBITMQ_USER: str = Field(validation_alias="RABBITMQ_USER")
    RABBITMQ_PASSWORD: SecretStr = Field(validation_alias="RABBITMQ_PASSWORD")
    RABBITMQ_HOST: str = Field(validation_alias="RABBITMQ_HOST")
    RABBITMQ_PORT: int = Field(validation_alias="RABBITMQ_PORT")
    RABBITMQ_EXCHANGE: str = Field(default="fundamental.events", validation_alias="RABBITMQ_EXCHANGE")
    RABBITMQ_REPORT_QUEUE: str = Field(default="report.published", validation_alias="RABBITMQ_REPORT_QUEUE")
    RABBITMQ_PRICE_QUEUE: str = Field(default="price.updated", validation_alias="RABBITMQ_PRICE_QUEUE")

    # gRPC → market-service
    MARKET_SERVICE_HOST: str = Field(default="market-service", validation_alias="MARKET_SERVICE_HOST")
    MARKET_SERVICE_PORT: int = Field(default=50051, validation_alias="MARKET_SERVICE_PORT")
    GRPC_TIMEOUT: float = Field(default=5.0, validation_alias="GRPC_TIMEOUT")

    # Polygon.io
    POLYGON_KEY: SecretStr = Field(validation_alias="POLYGON_KEY")
    POLYGON_BASE_URL: str = Field(default="https://api.polygon.io", validation_alias="POLYGON_BASE_URL")

    # Alpha Vantage (fallback)
    ALPHA_VANTAGE_KEY: SecretStr = Field(validation_alias="ALPHA_VANTAGE_KEY")
    ALPHA_VANTAGE_BASE_URL: str = Field(default="https://www.alphavantage.co", validation_alias="ALPHA_VANTAGE_BASE_URL")

    # Celery
    CELERY_RESULT_BACKEND_DB: str = Field(default="1", validation_alias="CELERY_RESULT_BACKEND_DB")
    CELERY_NIGHTLY_IMPORT_HOUR: int = Field(default=2, validation_alias="CELERY_NIGHTLY_IMPORT_HOUR")
    CELERY_NIGHTLY_IMPORT_MINUTE: int = Field(default=0, validation_alias="CELERY_NIGHTLY_IMPORT_MINUTE")


    # ── Computed URLs ──────────────────────────────────────────────────────────

    @property
    def db_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB_NAME}"
        )

    @property
    def db_migrations_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.REDIS_PASSWORD.get_secret_value()}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )

    @property
    def redis_celery_url(self) -> str:
        return (
            f"redis://:{self.REDIS_PASSWORD.get_secret_value()}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.CELERY_RESULT_BACKEND_DB}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:"
            f"{self.RABBITMQ_PASSWORD.get_secret_value()}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
        )

    @property
    def grpc_address(self) -> str:
        return f"{self.MARKET_SERVICE_HOST}:{self.MARKET_SERVICE_PORT}"


settings = Config()  # type: ignore
