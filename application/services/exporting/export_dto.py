from typing import Optional
from pydantic import BaseModel,validator
from uuid import UUID
class NotesExport(BaseModel):
    """DTO dla exportowania notes

    exportuje notes do pliku txt:
    - plikowi nada jest nazwa notes.title(decrypted)
    - zawartość jest nadawana z notes.content(decrypted)
    """
    
    note_id:int
    user_uuid:UUID

    @validator("note_id")
    def _validate_id(cls,id):
        """upewniamy się że notatka o podany id istnieje"""
        if not id or not isinstance(id,int):
            raise ValueError("id nie istnieje")
        return id
    
    @validator("user_uuid")
    def _validate_user_uuid(cls, value):
        """Ensure user_uuid is a valid UUID."""
        if not isinstance(value, UUID):
            raise ValueError("user_uuid must be a valid UUID")
        return value
    class Config:
        str_strip_whitespace = True
        validate_assignment = True