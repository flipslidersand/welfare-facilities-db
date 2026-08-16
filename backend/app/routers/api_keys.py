from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List
from app.database import get_db
from app.models import ApiKey
from app.auth import hash_api_key, generate_api_key, require_api_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    last_used_at: datetime | None
    usage_count: int

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyResponse):
    key: str


class ApiKeyUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    expires_at: datetime | None = None


@router.get("", response_model=List[ApiKeyResponse], dependencies=[Depends(require_api_key)])
async def list_api_keys(db: Session = Depends(get_db)):
    keys = db.query(ApiKey).all()
    return keys


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
async def create_api_key(request: ApiKeyCreateRequest, db: Session = Depends(get_db)):
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)

    api_key = ApiKey(
        key_hash=key_hash,
        name=request.name,
        expires_at=request.expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        key=plain_key
    )


@router.patch("/{key_id}", response_model=ApiKeyResponse, dependencies=[Depends(require_api_key)])
async def update_api_key(key_id: int, request: ApiKeyUpdateRequest, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if request.name is not None:
        api_key.name = request.name
    if request.is_active is not None:
        api_key.is_active = request.is_active
    if request.expires_at is not None:
        api_key.expires_at = request.expires_at

    db.commit()
    db.refresh(api_key)
    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)])
async def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    db.delete(api_key)
    db.commit()
