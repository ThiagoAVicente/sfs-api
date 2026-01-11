from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import secrets
import os

API_KEY:str|None = os.getenv("API_KEY")
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=True,
    description="Enter your API key"
)

async def verify_api_key(api_key: str = Security(api_key_header)):

    if not API_KEY or not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key
