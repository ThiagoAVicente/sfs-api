from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import secrets
import os

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=True,
    description="Enter your API key"
)

async def verify_api_key(api_key: str = Security(api_key_header)):

    expected_key:str|None = os.getenv("API_KEY")
    if not expected_key or not expected_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key
