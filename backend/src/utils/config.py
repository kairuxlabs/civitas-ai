# backend/src/utils/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str = ""
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    # Optional knowledge-layer services (in-memory fallbacks when unset)
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_timeout_seconds: float = 10.0
    # Optional — X-API-Key auth on mutating endpoints. Empty = auth disabled
    # (no-op), the default for local/dev/test.
    api_key: str = ""
    # Allowed CORS origins, comma-separated. Defaults cover the Vite dev
    # server and the deployed Vercel frontend.
    cors_origins: str = "http://localhost:3000,https://frontend-eta-six-46.vercel.app"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("database_url")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        # Normalize scheme for asyncpg
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                v = "postgresql+asyncpg://" + v[len(prefix):]
                break
        # asyncpg uses ssl=require, not sslmode=require
        v = v.replace("sslmode=require", "ssl=require")
        # asyncpg doesn't support channel_binding parameter
        v = v.replace("&channel_binding=require", "").replace("channel_binding=require&", "").replace("channel_binding=require", "")
        return v


settings = Settings()
