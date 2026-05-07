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

    app_name: str = Field(default="notification-service", validation_alias="APP_NAME")
    debug: bool = Field(default=False, validation_alias="DEBUG")

    rabbitmq_user: str = Field(validation_alias="RABBITMQ_USER")
    rabbitmq_password: SecretStr = Field(validation_alias="RABBITMQ_PASSWORD")
    rabbitmq_host: str = Field(validation_alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(validation_alias="RABBITMQ_PORT")

    redis_password: SecretStr = Field(validation_alias="REDIS_PASSWORD")
    redis_host: str = Field(validation_alias="REDIS_HOST")
    redis_port: str = Field(validation_alias="REDIS_PORT")
    redis_notifications_db: str = Field(default="5", validation_alias="REDIS_NOTIFICATIONS_DB")

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:"
            f"{self.rabbitmq_password.get_secret_value()}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )

settings = Config()  # type: ignore