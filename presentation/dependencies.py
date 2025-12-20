"""Dependency injection for FastAPI application.

This module provides dependency functions for repositories, services, and use cases.
"""

from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import Depends

from infrastructure.repositories.in_memory_note_repo import InMemoryNoteRepository
from infrastructure.repositories.in_memory_trash_repo import InMemoryTrashRepository
from infrastructure.config.settings import settings
from domain.interfaces import NoteRepository, TrashRepository

from application.services.encryption_service import EncryptionService
from application.services.filtering.filtering_service import FilteringService
from application.services.search.search_service import SearchService
from application.services.exporting.export_service import ExportingService
from application.services.self_delete_x_time import Delete_X_Time

from application.use_cases.notes.create_note import CreateNoteUseCase
from application.use_cases.notes.get_note import GetNoteUseCase
from application.use_cases.notes.edit_note import EditNoteUseCase
from application.use_cases.notes.notes_filtering import FilterNotesUseCase
from application.use_cases.notes.search_notes import SearchNotesUseCase
from application.use_cases.notes.export_note import ExportNoteUseCase

from application.use_cases.trashcan.trash_the_note import TrashNoteUseCase
from application.use_cases.trashcan.trash_note_get import TrashGetterUseCase
from application.use_cases.trashcan.trash_restore import TrashRestoreUseCase
from application.use_cases.trashcan.trash_perament import PermamentDelitionUseCase
from application.use_cases.trashcan.filter_trash import FilterTrashUseCase
from application.use_cases.trashcan.search_trash import SearchTrashUseCase

if TYPE_CHECKING:
    pass


# Repository dependencies
@lru_cache()
def get_note_repository() -> NoteRepository:
    """Get note repository instance (singleton)."""
    return InMemoryNoteRepository()


@lru_cache()
def get_trash_repository() -> TrashRepository:
    """Get trash repository instance (singleton)."""
    return InMemoryTrashRepository()


# Service dependencies
@lru_cache()
def get_encryption_service() -> EncryptionService:
    """Get encryption service instance (singleton)."""
    return EncryptionService(settings.SERVER_KEY)


def get_filtering_service(
    encryption: EncryptionService = Depends(get_encryption_service),
    note_repo: NoteRepository = Depends(get_note_repository),
    trash_repo: TrashRepository = Depends(get_trash_repository),
) -> FilteringService:
    """Get filtering service instance."""
    return FilteringService(encryption, note_repo, trash_repo)


def get_search_service(
    encryption: EncryptionService = Depends(get_encryption_service),
    note_repo: NoteRepository = Depends(get_note_repository),
    trash_repo: TrashRepository = Depends(get_trash_repository),
) -> SearchService:
    """Get search service instance."""
    return SearchService(encryption, note_repo, trash_repo)


def get_export_service(
    note_repo: NoteRepository = Depends(get_note_repository),
    encryption: EncryptionService = Depends(get_encryption_service),
) -> ExportingService:
    """Get export service instance."""
    return ExportingService(note_repo, encryption)


def get_self_delete_service(
    trash_repo: TrashRepository = Depends(get_trash_repository),
) -> Delete_X_Time:
    """Get self-delete service instance."""
    return Delete_X_Time(trash_repo, ttl_seconds=4)


# Use case dependencies - Notes
def get_create_note_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    encryption: EncryptionService = Depends(get_encryption_service),
) -> CreateNoteUseCase:
    """Get create note use case."""
    return CreateNoteUseCase(note_repo, encryption)


def get_get_note_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    encryption: EncryptionService = Depends(get_encryption_service),
) -> GetNoteUseCase:
    """Get get note use case."""
    return GetNoteUseCase(note_repo, encryption)


def get_edit_note_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    encryption: EncryptionService = Depends(get_encryption_service),
) -> EditNoteUseCase:
    """Get edit note use case."""
    return EditNoteUseCase(note_repo, encryption)


def get_filter_notes_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    filtering_service: FilteringService = Depends(get_filtering_service),
) -> FilterNotesUseCase:
    """Get filter notes use case."""
    return FilterNotesUseCase(note_repo, filtering_service)


def get_search_notes_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    search_service: SearchService = Depends(get_search_service),
) -> SearchNotesUseCase:
    """Get search notes use case."""
    return SearchNotesUseCase(note_repo, search_service)


def get_export_note_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    export_service: ExportingService = Depends(get_export_service),
) -> ExportNoteUseCase:
    """Get export note use case."""
    return ExportNoteUseCase(note_repo, export_service)


# Use case dependencies - Trash
def get_trash_note_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    trash_repo: TrashRepository = Depends(get_trash_repository),
) -> TrashNoteUseCase:
    """Get trash note use case."""
    return TrashNoteUseCase(note_repo, trash_repo)


def get_trash_getter_use_case(
    trash_repo: TrashRepository = Depends(get_trash_repository),
    encryption: EncryptionService = Depends(get_encryption_service),
) -> TrashGetterUseCase:
    """Get trash getter use case."""
    return TrashGetterUseCase(trash_repo, encryption)


def get_trash_restore_use_case(
    note_repo: NoteRepository = Depends(get_note_repository),
    trash_repo: TrashRepository = Depends(get_trash_repository),
) -> TrashRestoreUseCase:
    """Get trash restore use case."""
    return TrashRestoreUseCase(note_repo, trash_repo)


def get_permanent_delete_use_case(
    trash_repo: TrashRepository = Depends(get_trash_repository),
) -> PermamentDelitionUseCase:
    """Get permanent delete use case."""
    return PermamentDelitionUseCase(trash_repo)


def get_filter_trash_use_case(
    trash_repo: TrashRepository = Depends(get_trash_repository),
    filtering_service: FilteringService = Depends(get_filtering_service),
) -> FilterTrashUseCase:
    """Get filter trash use case."""
    return FilterTrashUseCase(trash_repo, filtering_service)


def get_search_trash_use_case(
    trash_repo: TrashRepository = Depends(get_trash_repository),
    search_service: SearchService = Depends(get_search_service),
) -> SearchTrashUseCase:
    """Get search trash use case."""
    return SearchTrashUseCase(trash_repo, search_service)

