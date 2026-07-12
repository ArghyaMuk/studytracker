from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "quiz-service"
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/studypilot_quizzes"
    curriculum_service_url: str = "http://localhost:8002"
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    upload_dir: str = "/tmp/pyq_uploads"

    class Config:
        env_file = ".env"


settings = Settings()
