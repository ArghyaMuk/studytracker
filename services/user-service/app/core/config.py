from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "user-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_users"

    class Config:
        env_file = ".env"


settings = Settings()
