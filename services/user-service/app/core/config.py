from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "user-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_users"
    admin_email: str = "admin@studypilot.com"
    admin_password: str = "Admin@1234"

    class Config:
        env_file = ".env"


settings = Settings()
