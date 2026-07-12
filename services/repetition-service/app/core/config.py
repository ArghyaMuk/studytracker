from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "repetition-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_repetition"
    user_service_url: str = "http://localhost:8001"

    class Config:
        env_file = ".env"


settings = Settings()
