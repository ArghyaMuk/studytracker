from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "curriculum-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_curriculum"

    class Config:
        env_file = ".env"


settings = Settings()
