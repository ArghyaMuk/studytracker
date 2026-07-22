from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings shared by all microservices."""

    # Database
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ
    rabbitmq_url: str = "amqp://arghya:arghya@localhost:5672/"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Service info
    service_name: str = "base-service"
    service_version: str = "1.0.0"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
