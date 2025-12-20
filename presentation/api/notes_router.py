import base64
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Optional, cast
from datetime import date

from presentation.schemas import NoteIn, NoteEdit
from presentation import dependencies as deps

from application.services.filtering.filter_dto import NotesFilter
from application.services.search.search_dto import NotesSearchQuery
from application.services.exporting.export_dto import NotesExport

from domain.interfaces import NoteRepository, TrashRepository
from application.services.encryption_service import EncryptionService
from application.services.filtering.filtering_service import FilteringService
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

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=dict)
async def create(
    note_in: NoteIn,
    tag: Optional[str] = None,
    create_use_case: CreateNoteUseCase = Depends(deps.get_create_note_use_case),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Tworzy notatkę:
    - generuje parę kluczy NaCl (prywatny i publiczny) dla klienta
    - szyfruje zawartość notatki lokalnie (hybrydowo) przy użyciu klucza publicznego klienta
    - przekazuje zaszyfrowaną zawartość do CreateNoteUseCase wraz z kluczem prywatnym klienta (base64)
    - zwraca ID notatki, klucz prywatny klienta (base64), klucz publiczny klienta (base64), zaszyfrowaną zawartość serwera i lokalnie
    """
    client_priv, client_pub = encryption_service.generate_nacl_keypair()
    client_priv_b64 = base64.b64encode(client_priv).decode()

    lokalny_pakiet_szyfrowany = encryption_service.encrypt_for_recipient(note_in.content, client_pub)
    lokalny_title_szyfrowany = encryption_service.encrypt_for_recipient(note_in.title, client_pub)
    lokalny_pakiet = lokalny_pakiet_szyfrowany.decode()
    lokalny_title = lokalny_title_szyfrowany.decode()

    note = await create_use_case.execute(
        lokalny_pakiet,
        client_private_key_b64=client_priv_b64,
        title=lokalny_title,
        tags=tag
    )

    return {
        "id": note.id,
        "client_private_key": client_priv_b64,
        "client_public_key": base64.b64encode(client_pub).decode(),
        "server encrypted": note.content.decode(),
        "title": note.title.decode(),
        "tags": note.tags,
        "local_encrypted": lokalny_pakiet,
        "created_at": note.created_at,
    }


@router.get("/{note_id}", response_model=dict)
async def get(
    note_id: int,
    klucz_prywatny: str,
    get_use_case: GetNoteUseCase = Depends(deps.get_get_note_use_case),
    note_repo: NoteRepository = Depends(deps.get_note_repository),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Pobieranie notatek dla wskazanego ID:
    - Pobiera zaszyfrowaną lokalnie zawartość notatki (po odszyfrowaniu serwerowym).
    - Odszyfrowuje lokalny pakiet przy użyciu podanego `klucz_prywatny` (base64).
    - Zwraca ID notatki i odszyfrowany tekst (content).
    """
    content = await get_use_case.execute(note_id)
    title = await get_use_case.title_execute(note_id)
    tag = await note_repo.get_note_by_id(note_id)

    if content is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")

    bity_klucza_priv = base64.b64decode(klucz_prywatny)
    try:
        text = encryption_service.decrypt_with_private(content.encode(), bity_klucza_priv)
        file_name = encryption_service.decrypt_with_private(title.encode(), bity_klucza_priv)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło się: {e}")

    return {
        "id": note_id,
        "content": text,
        "title": file_name,
        "tags": tag.tags if tag is not None else None,
        "created_at": tag.created_at if tag is not None else None
    }


@router.patch("/{note_id}", response_model=dict)
async def update_note(
    note_id: int,
    edit: NoteEdit,
    key_priv: str,
    new_title: Optional[str] = None,
    new_tags: Optional[str] = None,
    get_use_case: deps.GetNoteUseCase = Depends(deps.get_get_note_use_case),
    edit_use_case: EditNoteUseCase = Depends(deps.get_edit_note_use_case),
    note_repo: NoteRepository = Depends(deps.get_note_repository),
    encryption_service: deps.EncryptionService = Depends(deps.get_encryption_service),
):
    """Edit flow:
    - Pobiera zapisany lokalny pakiet (po odszyfrowaniu serwerowym).
    - Próbuje odszyfrować go podanym `client_private_key_b64` aby zweryfikować prawo do edycji.
    - Jeśli klucz poprawny, bierze `new_plaintext`, wygeneruje nową parę NaCl,
      zaszyfruje `new_plaintext` lokalnie (hybrydowo) i zapisze wynik na serwerze (serwerowa warstwa Fernet).
    - Zwraca nowy prywatny klucz klienta (base64), publiczny klucz (base64) i nowy lokalny pakiet (str).
    """
    old_tags = await note_repo.get_note_by_id(note_id)
    local_pkg = await get_use_case.execute(note_id)
    title_pkg = await get_use_case.title_execute(note_id)

    if local_pkg is None or local_pkg == "None":
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")

    try:
        priv_bytes = base64.b64decode(key_priv)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid base64 for client_private_key_b64")

    try:
        _current_plain = encryption_service.decrypt_with_private(local_pkg.encode(), priv_bytes)
        title_plain = encryption_service.decrypt_with_private(title_pkg.encode(), priv_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"tutaj się coś psuje: {e}")

    new_plaintext = edit.new_plaintext
    replace_title = new_title if new_title is not None else title_plain
    new_tag = new_tags if new_tags is not None else (old_tags.tags if old_tags is not None else None)

    new_priv, new_pub = encryption_service.generate_nacl_keypair()
    new_priv_b64 = base64.b64encode(new_priv).decode()

    new_local_package_bytes = encryption_service.encrypt_for_recipient(new_plaintext, new_pub)
    new_local_package = new_local_package_bytes.decode()

    new_local_title_bytes = encryption_service.encrypt_for_recipient(replace_title, new_pub)
    new_local_title = new_local_title_bytes.decode()

    updated_note = await edit_use_case.execute(
        note_id,
        new_local_package,
        new_client_private_key_b64=new_priv_b64,
        new_title=new_local_title,
        new_tags=new_tag
    )
    if updated_note is None:
        raise HTTPException(status_code=500, detail="failed to update note")

    return {
        "id": note_id,
        "new_client_private_key_b64": new_priv_b64,
        "new_client_public_key_b64": base64.b64encode(new_pub).decode(),
        "new_local_encrypted": new_local_package,
        "plaintext_saved": new_plaintext,
        "new_title": replace_title,
        "tags": new_tag,
    }


@router.get("/", response_model=list)
async def get_all_notes(
    get_use_case: GetNoteUseCase = Depends(deps.get_get_note_use_case),
    note_repo: NoteRepository = Depends(deps.get_note_repository),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Pobiera wszystkie notatki (tylko do celów testowych w produkcji będzie dozwolone ale po zalogowaniu(account locked)):
    - Pobiera wszystkie notatki z repozytorium.
    - Dla każdej notatki odszyfrowuje lokalny pakiet przy użyciu przechowywanego klucza prywatnego (jeśli dostępny).
    """
    all_notes = await note_repo.get_all()
    result = []
    if not all_notes:
        raise HTTPException(status_code=404)

    for note in all_notes:
        decrypted_content = await get_use_case.execute(note.id)
        decrypt_title = await get_use_case.title_execute(note.id)

        prive_key = base64.b64decode(note.key_private_b64) if note.key_private_b64 else None

        try:
            decrypted_content = encryption_service.decrypt_with_private(decrypted_content.encode(), prive_key) if prive_key else "No private key stored"
            decrypt_title = encryption_service.decrypt_with_private(decrypt_title.encode(), prive_key) if prive_key else "No private key stored"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło {e}")

        result.append({
            "id": note.id,
            "title": decrypt_title,
            "content": decrypted_content,
            "tags": note.tags,
            "private_key": note.key_private_b64,
            "created_at": note.created_at,
        })

    return result


@router.delete("/{note_id}", response_model=dict)
async def delete_note(
    note_id: int,
    trash_note_use_case: TrashNoteUseCase = Depends(deps.get_trash_note_use_case),
):
    """Przenosi notatkę do kosza
    - usuwa notatkę z repozytorium notatek
    - dodaje notatkę do repozytorium kosza z aktualnym timestampem
    """
    success = await trash_note_use_case.execute(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"message": "Notatka została przeniesiona do kosza"}


@router.get("/trash/", response_model=list)
async def get_trashed_notes(
    trash_repo: TrashRepository = Depends(deps.get_trash_repository),
    trash_getter_use_case: TrashGetterUseCase = Depends(deps.get_trash_getter_use_case),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Pobiera notatki znajdujące się w koszu
    - pobiera wszystkie notatki z repozytorium kosza
    - dla każdej notatki odszyfrowuje lokalny pakiet przy użyciu przechowywanego klucza prywatnego (jeśli dostępny)
    - zwraca listę notatek z ich ID, odszyfrowaną zawartością, czasem przeniesienia do kosza i kluczem prywatnym (base64)
    """
    trashed = await trash_repo.get_all_trashed()
    result = []

    for note in trashed:
        decrypted = await trash_getter_use_case.execute(note.id)
        decrypted_title = await trash_getter_use_case.execute_title(note.id)

        privkey = base64.b64decode(note.key_private_b64) if note.key_private_b64 else None
        try:
            decrypt = encryption_service.decrypt_with_private(decrypted.encode(), privkey) if privkey else "nie ma klucza prywatnego"
            decrypt_title = encryption_service.decrypt_with_private(decrypted_title.encode(), privkey) if privkey else "nie ma klucza prywatnego"
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
    trash_restore_use_case: TrashRestoreUseCase = Depends(deps.get_trash_restore_use_case),
):
    """Przywraca z kosza do notes
    - usuwa notatkę z repozytorium kosza
    - dodaje notatkę z powrotem do repozytorium notatek wraz z oryginalnymi danymi czyli kluczami i zawartością
    """
    to_restore = await trash_restore_use_case.execute(note_id)
    if to_restore is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu")
    return "Notatka została przywrócona z kosza"


@router.delete("/trash/permanent/{note_id}", response_model=str)
async def permament_deletion(
    note_id: int,
    permament_delete_use_case: PermamentDelitionUseCase = Depends(deps.get_permanent_delete_use_case),
):
    """Manualne permamentne usuwanie z kosza"""
    result = await permament_delete_use_case.execute(note_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu")
    return "usunięto na stałe(a to długi okres czasu)"


@router.delete("/trash/after_time", response_model=dict)
async def auto_delete(
    self_delete_service: Delete_X_Time = Depends(deps.get_self_delete_service),
):
    """Automatyczne usuwanie notatek z kosza po przekroczeniu czasu TTL.
    
    - Sprawdza wszystkie notatki w koszu
    - Usuwa na stałe te, które przekroczyły czas życia (TTL)
    - Zwraca liczbę usuniętych notatek
    """
    deleted_count = await self_delete_service.execute_all()
    return {
        "message": f"Automatycznie usunięto {deleted_count} notatek z kosza",
        "deleted_count": deleted_count
    }

@router.post("/filter", response_model=list)
async def filter_notes_endpoint(
    title: Optional[str] = None,
    tag: Optional[str] = None,
    date_eq: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
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
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Błędne parametry filtrów: {e}")

    notes = await filtering_service.filter_notes(note_repo, filters)

    result = []
    for note in notes:
        title_decrypt = await get_use_case.title_execute(note.id)
        content_decrypt = await get_use_case.execute(note.id)

        privkey = base64.b64decode(note.key_private_b64) if note.key_private_b64 else None

        decrypt_title = encryption_service.decrypt_with_private(title_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        content_decrypt = encryption_service.decrypt_with_private(content_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        result.append({
            "id": note.id,
            "title": decrypt_title,
            "content": content_decrypt,
            "tags": note.tags,
            "private_key": note.key_private_b64,
            "created_at": note.created_at,
        })

    return result


@router.post("/trash/filter", response_model=list)
async def filter_trash_endpoint(
    title: Optional[str] = None,
    tag: Optional[str] = None,
    date_eq: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
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
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Błędne parametry filtrów: {e}")

    trashed = await filtering_service.filter_trash(trash_repo, filters)

    result = []
    for trash in trashed:
        title_decrypt = await get_use_case.title_execute(trash.id)
        content_decrypt = await get_use_case.execute(trash.id)

        privkey = base64.b64decode(trash.key_private_b64) if trash.key_private_b64 else None

        decrypt_title = encryption_service.decrypt_with_private(title_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        content_decrypt = encryption_service.decrypt_with_private(content_decrypt.encode(), privkey) if privkey else "nie ma klucza prywatnego"
        result.append({
            "id": trash.id,
            "title": decrypt_title,
            "content": content_decrypt,
            "tags": trash.tags,
            "private_key": trash.key_private_b64,
            "created_at": trash.created_at,
        })

    return result


@router.post("/search", response_model=list)
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


@router.post("/trash/search", response_model=list)
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


@router.get("/export/{note_id}")
async def export_note_endpoint(
    note_id: int,
    export_note_use_case: ExportNoteUseCase = Depends(deps.get_export_note_use_case),
):
    """Eksportuje notatkę do pliku tekstowego.
    
    - Odszyfrowuje tytuł i zawartość notatki
    - Tworzy plik .txt o nazwie równej tytułowi notatki
    - Zawartość pliku to odszyfrowana treść notatki
    - Zwraca plik do pobrania
    """
    try:
        export_request = NotesExport(note_id=note_id)
        file_path, filename = await export_note_use_case.execute(export_request)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Nie udało się utworzyć pliku")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas eksportu: {str(e)}")
