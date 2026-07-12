from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "session-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_sessions"
    curriculum_service_url: str = "http://localhost:8002"

    class Config:
        env_file = ".env"


settings = Settings()
