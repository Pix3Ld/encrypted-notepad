from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: int
    email: str
    password_hash: str
    uuid: UUID
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Note(BaseModel):
    id: int
    title: bytes
    content: bytes
    user_uuid: UUID
    created_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    key_private_b64: Optional[str] = None
    public_key_b64: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Trash(BaseModel):
    id: int
    title: bytes
    content: bytes
    user_uuid: UUID
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    trashed_at: datetime
    key_private_b64: Optional[str] = None
    public_key_b64: Optional[str] = None