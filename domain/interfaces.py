from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from .entities import Note, Trash, User
from application.services.search.search_dto import NotesSearchQuery
from application.services.filtering.filter_dto import NotesFilter


class NoteRepository(ABC):

    @abstractmethod
    async def add(self, note: Note) -> Note:
        """Dodaj nową notatkę i zwróć ją (z ID)."""
        pass

    @abstractmethod
    async def get_by_id(self, *,note_id: int,user_uuid: UUID) -> Optional[Note]:
        pass

    @abstractmethod
    async def get_all(self,*, user_uuid: UUID) -> List[Note]:
        pass

    @abstractmethod
    async def update(
        self,
        note_id: int,
        *,
        user_uuid: UUID,
        title: Optional[bytes] = None,
        content: Optional[bytes] = None,
        tags: Optional[List[str]] = None,
        updated_at: Optional[datetime] = None,
    ) -> Optional[Note]:
        pass

    @abstractmethod
    async def delete_notes(
        self,
        note_id: int,
        *,
        user_uuid: UUID
    ) -> bool:
        pass



class TrashRepository(ABC):

    @abstractmethod
    async def add_to_trash(self, trashed_note: Trash) -> Trash:
        pass

    @abstractmethod
    async def get_by_id(self, *,note_id: int,user_uuid:UUID) -> Optional[Trash]:
        pass

    @abstractmethod
    async def get_all(self, user_uuid: UUID) -> List[Trash]:
        pass

    @abstractmethod
    async def restore(self, *,note_id: int,user_uuid:UUID) -> Optional[Note]:
        pass

    @abstractmethod
    async def delete_permanently(self, *,note_id: int,user_uuid:UUID) -> bool:
        pass



class UserRepository(ABC):

    @abstractmethod
    async def add(self, username: str, password_hash: str, created_at: Optional[datetime] = None) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_all(self) -> List[User]:
        pass



class SearchServiceInterface(ABC):

    @abstractmethod
    async def search_notes(
        self,
        repo: NoteRepository,
        search_query: NotesSearchQuery,
        user_uuid:UUID
    ) -> List[Note]:
        pass

    @abstractmethod
    async def search_trash(
        self,
        repo: TrashRepository,
        search_query: NotesSearchQuery,
        user_uuid:UUID
    ) -> List[Trash]:
        pass



class FilteringServiceInterface(ABC):

    @abstractmethod
    async def filter_notes(
        self,
        repo: NoteRepository,
        filters: NotesFilter,
        user_uuid:UUID,
    ) -> List[Note]:
        pass

    @abstractmethod
    async def filter_trash(
        self,
        repo: TrashRepository,
        filters: NotesFilter,
        user_uuid:UUID,
    ) -> List[Trash]:
        pass


class ExportServiceInterface(ABC):

    @abstractmethod
    async def export(
        self,
        note_id: int,
        repo: NoteRepository,
        user_uuid: UUID
    ) -> tuple[str, str]:
        pass
