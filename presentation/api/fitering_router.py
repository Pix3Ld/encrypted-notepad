import base64
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, cast
from datetime import date
from uuid import UUID

from presentation import dependencies as deps

from application.services.filtering.filter_dto import NotesFilter

from domain.interfaces import  TrashRepository
from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService
from application.services.filtering.filtering_service import FilteringService
from application.common.utils import format_datetime_to_str

from application.use_cases.notes.get_note import GetNoteUseCase
from application.use_cases.notes.notes_filtering import FilterNotesUseCase
from application.use_cases.trashcan.filter_trash import FilterTrashUseCase

router = APIRouter(prefix="/filtering", tags=["filtering"], dependencies=[Depends(deps.get_hardcoded_auth)])

@router.post("/filter", response_model=list)
async def filter_notes_endpoint(
    title: Optional[str] = None,
    tag: Optional[str] = None,
    date_eq: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    filtering_service: FilteringService = Depends(deps.get_filtering_service),
    filter_notes_use_case: FilterNotesUseCase = Depends(deps.get_filter_notes_use_case),
    get_use_case: GetNoteUseCase = Depends(deps.get_get_note_use_case),
    note_repo: NoteRepository = Depends(deps.get_note_repository),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Filtruje notatki po tytule, tagu i dacie utworzenia (dd-mm-yy)."""
    try:
        filters = NotesFilter(
            title=title,
            tag=tag,
            date_eq=cast(date, date_eq),
            date_from=cast(date, date_from),
            date_to=cast(date, date_to),
            user_uuid=user_uuid,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Błędne parametry filtrów: {e}")

    notes = await filtering_service.filter_notes(note_repo, filters, user_uuid)

    result = []
    for note in notes:
        title_decrypt = await get_use_case.title_execute(note_id=note.id, user_uuid=user_uuid)
        content_decrypt = await get_use_case.execute(note_id=note.id, user_uuid=user_uuid)

        privkey = base64.b64decode(note.key_private_b64) if note.key_private_b64 else None

        decrypt_title = encryption_service.decrypt_with_private(title_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        content_decrypt = encryption_service.decrypt_with_private(content_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        result.append({
            "id": note.id,
            "title": decrypt_title,
            "content": content_decrypt,
            "tags": note.tags,
            "private_key": note.key_private_b64,
            "created_at": format_datetime_to_str(note.created_at),
        })

    return result


@router.post("/trash/filter", response_model=list)
async def filter_trash_endpoint(
    title: Optional[str] = None,
    tag: Optional[str] = None,
    date_eq: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    filtering_service: FilteringService = Depends(deps.get_filtering_service),
    filter_trash_use_case: FilterTrashUseCase = Depends(deps.get_filter_trash_use_case),
    get_use_case: GetNoteUseCase = Depends(deps.get_get_note_use_case),
    trash_repo: TrashRepository = Depends(deps.get_trash_repository),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Filtruje kosz po tytule, tagu i dacie utworzenia (created_at w Trash)."""
    try:
        filters = NotesFilter(
            title=title,
            tag=tag,
            date_eq=cast(date, date_eq),
            date_from=cast(date, date_from),
            date_to=cast(date, date_to),
            user_uuid=user_uuid,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Błędne parametry filtrów: {e}")

    trashed = await filtering_service.filter_trash(trash_repo, filters, user_uuid)

    result = []
    for trash in trashed:
        title_decrypt = await get_use_case.title_execute(note_id=trash.id, user_uuid=user_uuid)
        content_decrypt = await get_use_case.execute(note_id=trash.id, user_uuid=user_uuid)

        privkey = base64.b64decode(trash.key_private_b64) if trash.key_private_b64 else None

        decrypt_title = encryption_service.decrypt_with_private(title_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        content_decrypt = encryption_service.decrypt_with_private(content_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        result.append({
            "id": trash.id,
            "title": decrypt_title,
            "content": content_decrypt,
            "tags": trash.tags,
            "private_key": trash.key_private_b64,
            "created_at": format_datetime_to_str(trash.created_at),
        })

    return result