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
    app_name: str = Field(default="portfolio-service", validation_alias="APP_NAME")
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # PostgreSQL
    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(validation_alias="POSTGRES_PORT")
    postgres_db_name: str = Field(validation_alias="POSTGRES_PORTFOLIO_DB")

    # Redis — market prices (read-only)
    redis_password: SecretStr = Field(validation_alias="REDIS_PASSWORD")
    redis_host: str = Field(validation_alias="REDIS_HOST")
    redis_port: str = Field(validation_alias="REDIS_PORT")
    redis_market_db: str = Field(validation_alias="REDIS_MARKET_DB")       # db=1, цены от market-service

    # Redis — portfolio cache (pnl)
    redis_portfolio_db: str = Field(validation_alias="REDIS_PORTFOLIO_DB") # db=4, локальный кэш

    # RabbitMQ
    rabbitmq_user: str = Field(validation_alias="RABBITMQ_USER")
    rabbitmq_password: SecretStr = Field(validation_alias="RABBITMQ_PASSWORD")
    rabbitmq_host: str = Field(validation_alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(validation_alias="RABBITMQ_PORT")

    # gRPC → market-service (для GetLastPriceBatch в analytics)
    market_service_host: str = Field(default="market-service", validation_alias="MARKET_SERVICE_HOST")
    market_service_port: int = Field(default=50051, validation_alias="MARKET_SERVICE_PORT")
    grpc_timeout: float = Field(default=5.0, validation_alias="GRPC_TIMEOUT")

    # Cache TTLs
    pnl_cache_ttl: int = Field(default=30, validation_alias="PNL_CACHE_TTL")

    # Outbox relay
    outbox_relay_interval: float = Field(default=5.0, validation_alias="OUTBOX_RELAY_INTERVAL")

    # ── Computed URLs ──────────────────────────────────────────────────────────

    @property
    def db_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}"
        )

    @property
    def db_migrations_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db_name}"
        )

    @property
    def redis_market_url(self) -> str:
        return (
            f"redis://:{self.redis_password.get_secret_value()}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_market_db}"
        )

    @property
    def redis_portfolio_url(self) -> str:
        return (
            f"redis://:{self.redis_password.get_secret_value()}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_portfolio_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:"
            f"{self.rabbitmq_password.get_secret_value()}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )

    @property
    def grpc_address(self) -> str:
        return f"{self.market_service_host}:{self.market_service_port}"


settings = Config()  # type: ignore