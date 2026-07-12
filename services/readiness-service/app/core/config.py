from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "readiness-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_readiness"
    user_service_url: str = "http://localhost:8001"
    curriculum_service_url: str = "http://localhost:8002"
    session_service_url: str = "http://localhost:8003"
    repetition_service_url: str = "http://localhost:8004"

    class Config:
        env_file = ".env"


settings = Settings()
