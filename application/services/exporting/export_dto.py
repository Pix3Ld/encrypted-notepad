from typing import Optional
from pydantic import BaseModel,validator

class NotesExport(BaseModel):
    """DTO dla exportowania notes

    exportuje notes do pliku txt:
    - plikowi nada jest nazwa notes.title(decrypted)
    - zawartość jest nadawana z notes.content(decrypted)
    """
    
    note_id:int

    @validator("note_id")
    def _validate_id(cls,id):
        """upewniamy się że notatka o podany id istnieje"""
        if not id or not isinstance(id,int):
            raise ValueError("id nie istnieje")
        return id
    class Config:
        str_strip_whitespace = True
        validate_assignment = True