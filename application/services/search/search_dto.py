from typing import Optional
from pydantic import BaseModel, validator


class NotesSearchQuery(BaseModel):
    """DTO for searching notes by query string.
    
    The search query will be matched against:
    - Note title (decrypted)
    - Note content (decrypted)
    - Note tags
    
    Matching is case-insensitive and partial (substring match).
    """
    query: str

    @validator("query")
    def _validate_query(cls, value):
        """Ensure query is not empty after stripping whitespace."""
        if not value or not value.strip():
            raise ValueError("Search query cannot be empty")
        return value.strip()

    class Config:
        str_strip_whitespace = True
        validate_assignment = True

