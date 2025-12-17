from .entities import Note, Trash
from typing import List, Optional
from abc import ABC, abstractmethod

# Forward declaration for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from application.services.search.search_dto import NotesSearchQuery
    from application.services.filtering.filter_dto import NotesFilter

class NoteRepository(ABC):
    @abstractmethod
    async def add_note(self, note: Note):
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
    async def update_notes(self,note_id:int,new_content:bytes,new_title: Optional[bytes], new_tags: Optional[str]=None,created_at: Optional[str]=None) ->Optional[Note]:
        '''zmień zawartość ,opcjonalnie zmień tytuł i tagi '''
        pass
    @abstractmethod
    async def delete_notes(self,note_id:int)->bool:
        '''usuń notatki '''
    pass
class TrashRepository(ABC):
    @abstractmethod
    async def add_to_trash(self, trashed_note: Trash):
        """Dodaj notatkę do kosza (powinna zawierać `trashed_at`)."""
        pass
    @abstractmethod
    async def get_trashed_note_by_id(self, note_id: int) -> Optional[Trash]:
        """Zwróć obiekt `Trash` z kosza po `note_id`."""
        pass
    @abstractmethod
    async def get_all_trashed(self) -> List[Trash]:
        """Zwróć listę obiektów `Trash` przechowywanych w koszu."""
        pass
    @abstractmethod
    async def restore_note_from_trash(self, note_id: int) -> Optional[Note]:
        """Przywróć notatkę z kosza i zwróć ją jako `Note` (bez `trashed_at`)."""
        pass
    @abstractmethod
    async def delete_trashed_note_permanently(self, note_id: int) -> bool:
        """premamenta kasacja"""
        pass


class SearchServiceInterface(ABC):
    """Interface for search service operations.

    Defines the contract for searching notes by query string with loose matching.
    """

    @abstractmethod
    async def search_notes(self, repo: NoteRepository, search_query: "NotesSearchQuery") -> List[Note]:
        """Search for notes matching the query.

        Args:
            repo: Repository for accessing notes
            search_query: DTO containing the search query string

        Returns:
            List of notes where the query appears in title, content, or tags
        """
        pass

    @abstractmethod
    async def search_trash(self, repo: TrashRepository, search_query: "NotesSearchQuery") -> List[Trash]:
        """Search for trashed notes matching the query.

        Args:
            repo: Repository for accessing trashed notes
            search_query: DTO containing the search query string

        Returns:
            List of trashed notes where the query appears in title, content, or tags
        """
        pass


class FilteringServiceInterface(ABC):
    """Interface for filtering service operations.

    Defines the contract for filtering notes by exact matching on title, tag, and date.
    """

    @abstractmethod
    async def filter_notes(self, repo: NoteRepository, filters: "NotesFilter") -> List[Note]:
        """Filter notes by title, tag, and date.

        Args:
            repo: Repository for accessing notes
            filters: DTO containing filter criteria

        Returns:
            List of notes matching all filter criteria
        """
        pass

    @abstractmethod
    async def filter_trash(self, repo: TrashRepository, filters: "NotesFilter") -> List[Trash]:
        """Filter trashed notes by title, tag, and date.

        Args:
            repo: Repository for accessing trashed notes
            filters: DTO containing filter criteria

        Returns:
            List of trashed notes matching all filter criteria
        """
        pass