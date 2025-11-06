from .entities import Note
from typing import List, Optional
from abc import ABC, abstractmethod

class NoteRepository(ABC):
    @abstractmethod
    def add_note(self, note: Note) -> None:
        """Add a new note to the repository."""
        pass
    @abstractmethod
    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Retrieve a note by its ID."""
        pass
    @abstractmethod
    def get_all(self) -> List[Note]:
        """Retrieve all notes from the repository."""
        pass