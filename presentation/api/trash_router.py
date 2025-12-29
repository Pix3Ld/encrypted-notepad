import base64

from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from presentation import dependencies as deps

from domain.interfaces import  TrashRepository
from application.services.encryption_service import EncryptionService

from application.use_cases.trashcan.trash_the_note import TrashNoteUseCase
from application.use_cases.trashcan.trash_note_get import TrashGetterUseCase
from application.use_cases.trashcan.trash_restore import TrashRestoreUseCase
from application.use_cases.trashcan.trash_perament import PermamentDelitionUseCase

router = APIRouter(prefix="/trash", tags=["trashcan"], dependencies=[Depends(deps.get_hardcoded_auth)])

@router.delete("/{note_id}", response_model=dict)
async def delete_note(
    note_id: int,
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    trash_note_use_case: TrashNoteUseCase = Depends(deps.get_trash_note_use_case),
):
    """Przenosi notatkę do kosza
    - usuwa notatkę z repozytorium notatek
    - dodaje notatkę do repozytorium kosza z aktualnym timestampem
    """
    success = await trash_note_use_case.execute(note_id=note_id, user_uuid=user_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"message": "Notatka została przeniesiona do kosza"}

@router.get("/trash/", response_model=list)
async def get_trashed_notes(
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    trash_repo: TrashRepository = Depends(deps.get_trash_repository),
    trash_getter_use_case: TrashGetterUseCase = Depends(deps.get_trash_getter_use_case),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Pobiera notatki znajdujące się w koszu
    - pobiera wszystkie notatki z repozytorium kosza
    - dla każdej notatki odszyfrowuje lokalny pakiet przy użyciu przechowywanego klucza prywatnego (jeśli dostępny)
    - zwraca listę notatek z ich ID, odszyfrowaną zawartością, czasem przeniesienia do kosza i kluczem prywatnym (base64)
    """
    trashed = await trash_repo.get_all(user_uuid=user_uuid)
    result = []

    for note in trashed:
        decrypted = await trash_getter_use_case.execute(note_id=note.id, user_uuid=user_uuid, field="content")
        decrypted_title = await trash_getter_use_case.execute(note_id=note.id, user_uuid=user_uuid, field="title")

        privkey = base64.b64decode(note.key_private_b64) if note.key_private_b64 else None
        try:
            decrypt = encryption_service.decrypt_with_private(decrypted.encode(), privkey) if privkey and decrypted else "nie ma klucza prywatnego lub danych"
            decrypt_title = encryption_service.decrypt_with_private(decrypted_title.encode(), privkey) if privkey and decrypted_title else "nie ma klucza prywatnego lub danych"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło się: {e}")

        result.append({
            "id": note.id,
            "title": decrypt_title,
            "content": decrypt,
            "created_at": note.created_at,
            "tags": note.tags,
            "trashed_at": note.trashed_at,
            "private_key": note.key_private_b64
        })

    return result

@router.post("/trash/restore/{note_id}", response_model=str)
async def restore_trashed(
    note_id: int,
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    trash_restore_use_case: TrashRestoreUseCase = Depends(deps.get_trash_restore_use_case),
):
    """Przywraca z kosza do notes
    - usuwa notatkę z repozytorium kosza
    - dodaje notatkę z powrotem do repozytorium notatek wraz z oryginalnymi danymi czyli kluczami i zawartością
    """
    to_restore = await trash_restore_use_case.execute(note_id=note_id, user_uuid=user_uuid)
    if to_restore is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu")
    return "Notatka została przywrócona z kosza"

@router.delete("/trash/permanent/{note_id}", response_model=str)
async def permament_deletion(
    note_id: int,
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    permament_delete_use_case: PermamentDelitionUseCase = Depends(deps.get_permanent_delete_use_case),
):
    """Manualne permamentne usuwanie z kosza"""
    result = await permament_delete_use_case.execute(note_id=note_id, user_uuid=user_uuid)
    if not result:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu")
    return "usunięto na stałe(a to długi okres czasu)"