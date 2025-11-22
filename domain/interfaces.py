from .entities import Note
from typing import List, Optional
from abc import ABC, abstractmethod

class NoteRepository(ABC):
    @abstractmethod
    async def add_note(self, note: Note) -> None:
        """dodaj nową notatkę do repo"""
        pass
    @abstractmethod
    async def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Retrieve a note by its ID."""
        pass
    @abstractmethod
    async def get_all(self) -> List[Note]:
        """zgarnij wszystkie notatki"""
        pass
    @abstractmethod
    async def update_notes(self,note_id:int,new_content:bytes)->Optional[Note]:
        '''aktualizuje notatki istniejące'''
        pass
    @abstractmethod
    async def delete_notes(self,note_id:int)->bool:
        '''usuń notatki '''
    pass
class TrashRepository(ABC):
    @abstractmethod
    async def add_to_trash(self, trashed_note: Note) -> None:
        """notka do kosza"""
        pass
    @abstractmethod
    async def get_trashed_note_by_id(self, note_id: int) -> Optional[Note]:
        """zgarnij notkę po id"""
        pass
    @abstractmethod
    async def get_all_trashed(self) -> List[Note]:
        """zgarnij wsztko z kosza"""
        pass
    @abstractmethod
    async def restore_note_from_trash(self, note_id: int) -> Optional[Note]:
        """zwróć notkę """
        pass
    @abstractmethod
    async def delete_trashed_note_permanently(self, note_id: int) -> bool:
        """premamenta kasacja"""
        pass