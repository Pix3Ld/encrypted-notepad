"""Dependency injection for FastAPI application.

This module provides dependency functions for repositories, services, and use cases.
"""

from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import Depends
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials

from infrastructure.repositories.sql_note_repo import SQLNoteRepository
from infrastructure.repositories.sql_trash_repo import SQLTrashRepository
from infrastructure.config.settings import settings
from domain.interfaces import NoteRepository, TrashRepository, UserRepository
from domain.entities import User
from uuid import UUID

from application.services.encryption_service import EncryptionService
from application.services.filtering.filtering_service import FilteringService
from application.services.search.search_service import SearchService
from application.services.exporting.export_service import ExportingService
from application.services.self_delete_x_time import DeleteXTime
from infrastructure.repositories.sql_user_repo import SQLUserRepository
from application.services.user_service import UserService

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
    return SQLNoteRepository()


@lru_cache()
def get_trash_repository() -> TrashRepository:
    """Get trash repository instance (singleton)."""
    return SQLTrashRepository()


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
) -> DeleteXTime:
    """Get self-delete service instance."""
    return DeleteXTime(trash_repo)


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


# User dependencies
@lru_cache()
def get_user_repository() -> UserRepository:
    """Get user repository instance (singleton)."""
    return SQLUserRepository()


@lru_cache()
def get_user_service() -> UserService:
    """Get user service configured with JWT settings."""
    repo = get_user_repository()
    return UserService(repo, settings.JWT_SECRET, settings.JWT_EXP_SECONDS)


# OAuth2 scheme for dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


async def get_current_user(token: str = Depends(oauth2_scheme), user_service: UserService = Depends(get_user_service)):
    """Dependency that returns the current user if token is valid, otherwise raises 401."""
    data = user_service.decode_token(token)
    if not data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    user_id = data.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    # repo method returns user or None
    user = await user_service._repo.get_by_id(int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# HTTP Basic Auth that validates against database
basic_security = HTTPBasic()


async def get_hardcoded_auth(credentials: HTTPBasicCredentials = Depends(basic_security)):
    """HTTP Basic auth that validates credentials against the database.
    
    Use HTTP Basic auth with your registered email and password.
    """
    user_service = get_user_service()
    
    # Normalize input
    email = credentials.username.strip() if credentials.username else ""
    password = credentials.password.strip() if credentials.password else ""
    
    # Debug: print received credentials (remove in production)
    print(f"HTTP Basic Auth attempt - Email: '{email}'")
    
    # Validate against database
    token_info = await user_service.authenticate_user(email, password)
    if token_info is None:
        print(f"HTTP Basic Auth failed for email: '{email}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    print(f"HTTP Basic Auth successful for email: '{email}'")
    # Get user to return UUID if needed
    user = await user_service._repo.get_by_email(email)
    if user:
        return {"email": email, "user_uuid": user.uuid}
    return {"email": email}


async def get_user_uuid_from_basic_auth(credentials: HTTPBasicCredentials = Depends(basic_security)) -> UUID:
    """HTTP Basic auth that validates credentials and returns user UUID.
    
    Use HTTP Basic auth with your registered email and password.
    This can be used instead of token-based auth for endpoints that need user_uuid.
    """
    user_service = get_user_service()
    
    # Normalize input
    email = credentials.username.strip() if credentials.username else ""
    password = credentials.password.strip() if credentials.password else ""
    
    # Debug: print received credentials
    print(f"HTTP Basic Auth (UUID) attempt - Email: '{email}'")
    
    # Validate against database
    token_info = await user_service.authenticate_user(email, password)
    if token_info is None:
        print(f"HTTP Basic Auth (UUID) failed for email: '{email}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Get user to return UUID
    user = await user_service._repo.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    print(f"HTTP Basic Auth (UUID) successful for email: '{email}', UUID: {user.uuid}")
    return user.uuid


async def get_current_user_uuid(user: User = Depends(get_current_user)) -> UUID:
    """Dependency that returns the current user's UUID."""
    return user.uuid

