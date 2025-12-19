from .entities import Note, Trash
from typing import List, Optional
from abc import ABC, abstractmethod

# Deklaracja do przodu dla typu
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from application.services.search.search_dto import NotesSearchQuery
    from application.services.filtering.filter_dto import NotesFilter
    #from application.services.exporting.export_dto import

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
    """Interface dla search service operations.

    definuje szukanie notes przez query string z 'loose matching'.
    """

    @abstractmethod
    async def search_notes(self, repo: NoteRepository, search_query: "NotesSearchQuery") -> List[Note]:
        """szuaknie dla notes == query.

        argumenty:
            repo: Repository dla dostępu do notes
            search_query: DTO zawierający wysukiwane query string

        zwraca:
            Liste notes gdzie query pojawia się w title, content, or tags
        """
        pass

    @abstractmethod
    async def search_trash(self, repo: TrashRepository, search_query: "NotesSearchQuery") -> List[Trash]:
        """szuaknie dla trash == query.

        argumenty:
            repo: Repository dla dostępu do trash
            search_query: DTO zawierający wysukiwane query string

        zwraca:
            Liste trash gdzie query pojawia się w title, content, or tags
        """
        pass


class FilteringServiceInterface(ABC):
    """Interface dla filtering operacji service.

    definuje filtering dla notes dla wartości dokładnie rónej title, tag, and date.
    """

    @abstractmethod
    async def filter_notes(self, repo: NoteRepository, filters: "NotesFilter") -> List[Note]:
        """Filter notes przez title, tag, oraz date.

        argumenty:
            repo: Repository dla dostępu do notes
            filters: DTO zawierający wymogi filter 

        zwraca:
            Liste notes przez porównianie wszystkich kryteriów filtrowania 
        """
        pass

    @abstractmethod
    async def filter_trash(self, repo: TrashRepository, filters: "NotesFilter") -> List[Trash]:
        """Filter trash przez title, tag, oraz date.

        argumenty:
            repo: Repository dla dostępu do trash
            filters: DTO zawierający wymogi filter 

        zwraca:
            Liste trash przez porównianie wszystkich kryteriów filtrowania
        """
        pass

class ExportServiceInterface(ABC):
    @abstractmethod
    async def exporting(self, note_id: int, repo: NoteRepository) -> tuple[str, str]:
        """exportowanie danych z notes do pliku tekstowego 

        Args:
            note_id: ID notatki do wyeksportowania
            repo: Repository dla dostępu do notes
            
        Returns:
            Tuple zawierający (ścieżka do pliku, nazwa pliku)
        """
        pass