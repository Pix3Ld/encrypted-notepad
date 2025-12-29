from typing import Optional
from pydantic import BaseModel, validator
from uuid import UUID

class NotesSearchQuery(BaseModel):
    """DTO for searching notes by query string.
    
    The search query will be matched against:
    - Note title (decrypted)
    - Note content (decrypted)
    - Note tags
    
    Matching is case-insensitive and partial (substring match).
    """
    query: str
    user_uuid: UUID
    @validator("query")
    def _validate_query(cls, value):
        """Ensure query is not empty after stripping whitespace."""
        if not value or not value.strip():
            raise ValueError("Search query cannot be empty")
        return value.strip()
    @validator("user_uuid")
    def _validate_user_uuid(cls, value):
        """Ensure user_uuid is a valid UUID."""
        if not isinstance(value, UUID):
            raise ValueError("user_uuid must be a valid UUID")
        return value
    class Config:
        str_strip_whitespace = True
        validate_assignment = True

