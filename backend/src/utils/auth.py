# backend/src/utils/auth.py
from fastapi import Header, HTTPException

from src.utils.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency guarding mutating endpoints with a simple
    X-API-Key header check.

    No-op (auth disabled) when settings.api_key is empty — this is the
    default for local/dev/test, so existing callers keep working without a
    header. When settings.api_key is set, the request's X-API-Key header
    must match exactly, else 401.
    """
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
