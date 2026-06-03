from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./knowledgebase.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    PREVIEW_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "previews")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()
