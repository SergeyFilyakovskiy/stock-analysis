from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.types import SecretStr
from pydantic import Field
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent.parent.parent.parent / ".env"

class Config(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        case_sensitive=True,
        extra='ignore'
    )

    postgres_user: str = Field(validation_alias='POSTGRES_USER')
    postgres_password: SecretStr = Field(validation_alias='POSTGRES_PASSWORD')
    postgres_host: str = Field(validation_alias='POSTGRES_HOST')
    postgres_port: int = Field(validation_alias='POSTGRES_PORT')
    postgres_db_name: str = Field(validation_alias='POSTGRES_MARKET_DB')

    redis_password: SecretStr = Field(validation_alias='REDIS_PASSWORD')
    redis_host: str = Field(validation_alias='REDIS_HOST')
    redis_port: str = Field(validation_alias='REDIS_PORT')
    redis_db: str = Field(validation_alias='REDIS_MARKET_DB')

    rabbitmq_user: str = Field(validation_alias='RABBITMQ_USER')
    rabbitmq_password: SecretStr = Field(validation_alias='RABBITMQ_PASSWORD')
    rabbitmq_host: str = Field(validation_alias='RABBITMQ_HOST')
    rabbitmq_port: int = Field(validation_alias='RABBITMQ_PORT')

    jwt_secret: SecretStr = Field(validation_alias='JWT_SECRET')
    jwt_algorithm: str = Field(validation_alias='JWT_ALGORITHM')

    POLYGON_KEY: SecretStr = Field(validation_alias='POLYGON_KEY')
    ALPHA_VANTAGE_KEY: SecretStr = Field(validation_alias='ALPHA_VANTAGE_KEY')

    PRICE_FETCH_INTERVAL_SECONDS: int = Field(validation_alias='PRICE_FETCH_INTERVAL_SECONDS')

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
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password.get_secret_value()}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        )
    
    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password.get_secret_value()}@"\
            f"{self.rabbitmq_host}:{self.rabbitmq_port}/"




settings = Config()  # type: ignore