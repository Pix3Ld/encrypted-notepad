import base64

from fastapi import APIRouter, HTTPException, Depends
from presentation import dependencies as deps

from application.services.search.search_dto import NotesSearchQuery

from application.services.encryption_service import EncryptionService

from application.use_cases.trashcan.trash_note_get import TrashGetterUseCase
from application.use_cases.trashcan.search_trash import SearchTrashUseCase
from application.use_cases.notes.search_notes import SearchNotesUseCase


router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(deps.get_hardcoded_auth)])


@router.post("/", response_model=list)
async def search_notes_endpoint(
    query: str,
    search_notes_use_case: SearchNotesUseCase = Depends(deps.get_search_notes_use_case),
    get_use_case: deps.GetNoteUseCase = Depends(deps.get_get_note_use_case),
    encryption_service: deps.EncryptionService = Depends(deps.get_encryption_service),
):
    """Wyszukuje notatki po zapytaniu (luźne dopasowanie w tytule, treści i tagach).
    
    Wyszukiwanie jest case-insensitive i częściowe - jeśli wpiszesz np. "cze",
    znajdzie wszystkie notatki zawierające "cze" w tytule, treści lub tagach
    (np. "Czech", "czekolada", "position" itp.).
    """
    try:
        search_query = NotesSearchQuery(query=query)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Błędne parametry wyszukiwania: {e}")

    notes = await search_notes_use_case.execute(search_query)

    if not notes:
        return []

    result = []
    for note in notes:
        title_decrypt = await get_use_case.title_execute(note.id)
        content_decrypt = await get_use_case.execute(note.id)

        privkey = base64.b64decode(note.key_private_b64) if note.key_private_b64 else None

        try:
            decrypt_title = encryption_service.decrypt_with_private(title_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
            decrypt_content = encryption_service.decrypt_with_private(content_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło się: {e}")

        result.append({
            "id": note.id,
            "title": decrypt_title,
            "content": decrypt_content,
            "tags": note.tags,
            "private_key": note.key_private_b64,
            "created_at": note.created_at,
        })

    return result

@router.post("/trash/", response_model=list)
async def search_trash_endpoint(
    query: str,
    search_trash_use_case: SearchTrashUseCase = Depends(deps.get_search_trash_use_case),
    trash_getter_use_case: TrashGetterUseCase = Depends(deps.get_trash_getter_use_case),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Wyszukuje notatki w koszu po zapytaniu (luźne dopasowanie w tytule, treści i tagach).
    
    Wyszukiwanie jest case-insensitive i częściowe - jeśli wpiszesz np. "cze",
    znajdzie wszystkie notatki w koszu zawierające "cze" w tytule, treści lub tagach
    (np. "Czech", "czekolada", "position" itp.).
    """
    try:
        search_query = NotesSearchQuery(query=query)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Błędne parametry wyszukiwania: {e}")

    trashed = await search_trash_use_case.execute(search_query)

    if not trashed:
        return []

    result = []
    for trash in trashed:
        title_decrypt = await trash_getter_use_case.execute_title(trash.id)
        content_decrypt = await trash_getter_use_case.execute(trash.id)

        privkey = base64.b64decode(trash.key_private_b64) if trash.key_private_b64 else None

        try:
            decrypt_title = encryption_service.decrypt_with_private(title_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
            decrypt_content = encryption_service.decrypt_with_private(content_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło się: {e}")

        result.append({
            "id": trash.id,
            "title": decrypt_title,
            "content": decrypt_content,
            "tags": trash.tags,
            "private_key": trash.key_private_b64,
            "created_at": trash.created_at,
            "trashed_at": trash.trashed_at,
        })

    return result