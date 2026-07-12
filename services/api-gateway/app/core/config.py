from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "api-gateway"

    # Downstream service URLs
    user_service_url: str = "http://localhost:8001"
    curriculum_service_url: str = "http://localhost:8002"
    session_service_url: str = "http://localhost:8003"
    repetition_service_url: str = "http://localhost:8004"
    quiz_service_url: str = "http://localhost:8005"
    readiness_service_url: str = "http://localhost:8006"
    notification_service_url: str = "http://localhost:8007"

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
