"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date


class NoteIn(BaseModel):
    """Schema for creating a new note."""
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Locally encrypted content")


class NoteEdit(BaseModel):
    """Schema for editing a note."""
    new_plaintext: str = Field(..., description="New plaintext content to encrypt and save")


class NoteResponse(BaseModel):
    """Schema for note response."""
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    created_at: Optional[str] = None
    private_key: Optional[str] = None
    client_private_key: Optional[str] = None
    client_public_key: Optional[str] = None
    server_encrypted: Optional[str] = None
    local_encrypted: Optional[str] = None
    trashed_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "My Note",
                "content": "Note content",
                "tags": "work, important",
                "created_at": "01-01-24",
                "private_key": "base64_key"
            }
        }


class NoteCreateResponse(BaseModel):
    """Schema for note creation response."""
    id: int
    client_private_key: str
    client_public_key: str
    server_encrypted: str
    title: str
    tags: Optional[str] = None
    local_encrypted: str
    created_at: str


class NoteUpdateResponse(BaseModel):
    """Schema for note update response."""
    id: int
    new_client_private_key_b64: str
    new_client_public_key_b64: str
    new_local_encrypted: str
    plaintext_saved: str
    new_title: str
    tags: Optional[str] = None


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str


class UserIn(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token_type: str
    user_token: str
    expires: Optional[str]


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: Optional[str] = None

