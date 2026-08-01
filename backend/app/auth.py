import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY = os.getenv("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str = Security(api_key_header)) -> str:
    if not API_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API key not configured")
    if key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return key
