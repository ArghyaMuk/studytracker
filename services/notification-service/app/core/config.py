from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "notification-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_notifications"
    readiness_service_url: str = "http://localhost:8006"
    repetition_service_url: str = "http://localhost:8004"

    class Config:
        env_file = ".env"


settings = Settings()
