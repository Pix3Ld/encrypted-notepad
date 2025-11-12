from .entities import Note
from typing import List, Optional
from abc import ABC, abstractmethod

class NoteRepository(ABC):
    @abstractmethod
    async def add_note(self, note: Note) -> None:
        """Add a new note to the repository."""
        pass
    @abstractmethod
    async def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Retrieve a note by its ID."""
        pass
    @abstractmethod
    async def get_all(self) -> List[Note]:
        """Retrieve all notes from the repository."""
        pass
    @abstractmethod
    async def update_notes(self,note_id:int,new_content:bytes)->Optional[Note]:
        '''aktualizuje notatki istniejące'''
        pass
    @abstractmethod
    async def delete_notes(self,note_id:int)->bool:
        '''usuń notatki '''
        pass