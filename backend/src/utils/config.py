# backend/src/utils/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str = ""
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
