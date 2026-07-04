# backend/src/utils/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str = ""
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("database_url")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        if v.startswith("postgresql://") or v.startswith("postgres://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
