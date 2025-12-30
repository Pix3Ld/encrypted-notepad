import base64
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from uuid import UUID

from presentation.schemas import NoteIn, NoteEdit
from presentation import dependencies as deps

from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService
from application.common.utils import format_datetime_to_str

from application.use_cases.notes.create_note import CreateNoteUseCase
from application.use_cases.notes.get_note import GetNoteUseCase
from application.use_cases.notes.edit_note import EditNoteUseCase

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=dict)
async def create(
    note_in: NoteIn,
    tag: Optional[str] = None,
    user_uuid: UUID = Depends(deps.get_user_uuid_from_basic_auth),
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
        user_uuid=user_uuid,
        local_encrypted_content=lokalny_pakiet,
        client_private_key_b64=client_priv_b64,
        title=lokalny_title,
        tags=[tag] if tag else None
    )

    return {
        "id": note.id,
        "client_private_key": client_priv_b64,
        "client_public_key": base64.b64encode(client_pub).decode(),
        "server encrypted": note.content.decode(),
        "title": note.title.decode(),
        "tags": note.tags,
        "local_encrypted": lokalny_pakiet,
        "created_at": format_datetime_to_str(note.created_at),
    }


@router.get("/{note_id}", response_model=dict)
async def get(
    note_id: int,
    klucz_prywatny: str,
    user_uuid: UUID = Depends(deps.get_user_uuid_from_basic_auth),
    get_use_case: GetNoteUseCase = Depends(deps.get_get_note_use_case),
    note_repo: NoteRepository = Depends(deps.get_note_repository),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Pobieranie notatek dla wskazanego ID:
    - Pobiera zaszyfrowaną lokalnie zawartość notatki (po odszyfrowaniu serwerowym).
    - Odszyfrowuje lokalny pakiet przy użyciu podanego `klucz_prywatny` (base64).
    - Zwraca ID notatki i odszyfrowany tekst (content).
    """
    content = await get_use_case.execute(note_id=note_id, user_uuid=user_uuid)
    title = await get_use_case.title_execute(note_id=note_id, user_uuid=user_uuid)
    tag = await note_repo.get_by_id(note_id=note_id, user_uuid=user_uuid)

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
        "created_at": format_datetime_to_str(tag.created_at) if tag is not None else None
    }


@router.patch("/{note_id}", response_model=dict)
async def update_note(
    note_id: int,
    edit: NoteEdit,
    key_priv: str,
    new_title: Optional[str] = None,
    new_tags: Optional[str] = None,
    user_uuid: UUID = Depends(deps.get_user_uuid_from_basic_auth),
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
    old_tags = await note_repo.get_by_id(note_id=note_id, user_uuid=user_uuid)
    local_pkg = await get_use_case.execute(note_id=note_id, user_uuid=user_uuid)
    title_pkg = await get_use_case.title_execute(note_id=note_id, user_uuid=user_uuid)

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
    new_tag = [new_tags] if isinstance(new_tags, str) else (new_tags if new_tags is not None else (old_tags.tags if old_tags is not None else None))

    new_priv, new_pub = encryption_service.generate_nacl_keypair()
    new_priv_b64 = base64.b64encode(new_priv).decode()

    new_local_package_bytes = encryption_service.encrypt_for_recipient(new_plaintext, new_pub)
    new_local_package = new_local_package_bytes.decode()

    new_local_title_bytes = encryption_service.encrypt_for_recipient(replace_title, new_pub)
    new_local_title = new_local_title_bytes.decode()

    updated_note = await edit_use_case.execute(
        note_id=note_id,
        user_uuid=user_uuid,
        new_local_encrypted_content=new_local_package,
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
    user_uuid: UUID = Depends(deps.get_user_uuid_from_basic_auth),
    get_use_case: GetNoteUseCase = Depends(deps.get_get_note_use_case),
    note_repo: NoteRepository = Depends(deps.get_note_repository),
    encryption_service: EncryptionService = Depends(deps.get_encryption_service),
):
    """Pobiera wszystkie notatki (tylko do celów testowych w produkcji będzie dozwolone ale po zalogowaniu(account locked)):
    - Pobiera wszystkie notatki z repozytorium.
    - Dla każdej notatki odszyfrowuje lokalny pakiet przy użyciu przechowywanego klucza prywatnego (jeśli dostępny).
    """
    all_notes = await note_repo.get_all(user_uuid=user_uuid)
    result = []
    if not all_notes:
        raise HTTPException(status_code=404)

    for note in all_notes:
        decrypted_content = await get_use_case.execute(note_id=note.id, user_uuid=user_uuid)
        decrypt_title = await get_use_case.title_execute(note_id=note.id, user_uuid=user_uuid)

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
            "created_at": format_datetime_to_str(note.created_at),
        })

    return result
