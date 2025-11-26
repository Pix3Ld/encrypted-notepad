import base64

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from application.use_cases.create_note import CreateNoteUseCase
from application.use_cases.get_note import GetNoteUseCase
from application.use_cases.edit_note import EditNoteUseCase
from application.use_cases.delete_note import NoteDeleteUseCase

from application.use_cases.trashcan.trash_the_note import TrashNoteUseCase
from application.use_cases.trashcan.trash_note_get import TrashGetterUseCase
from application.use_cases.trashcan.trash_restore import TrashRestoreUseCase
from application.use_cases.trashcan.trash_perament import PermamentDelitionUseCase

from application.services.encryption_service import EncryptionService
from application.services.self_delete_x_time import Delete_X_Time

from infrastructure.repositories.in_memory_note_repo import InMemoryNoteRepository
from infrastructure.repositories.in_memory_trash_repo import InMemoryTrashRepository
from infrastructure.config.settings import settings

router=APIRouter(prefix="/notes",tags=["notes"])

# Dependency init
note_repo = InMemoryNoteRepository()
trash_repo = InMemoryTrashRepository()
encryption_service = EncryptionService(settings.SERVER_KEY)

# Note use cases
create_use_case = CreateNoteUseCase(note_repo, encryption_service)
get_use_case = GetNoteUseCase(note_repo, encryption_service)
edit_use_case = EditNoteUseCase(note_repo, encryption_service)
delete_note_use_case = NoteDeleteUseCase(note_repo)

# Trash use cases
trash_note_use_case = TrashNoteUseCase(note_repo, trash_repo)
trash_getter_use_case = TrashGetterUseCase(trash_repo, encryption_service)
trash_restore_use_case = TrashRestoreUseCase(note_repo, trash_repo)
permament_delete_use_case = PermamentDelitionUseCase(trash_repo)
self_delete_service = Delete_X_Time(trash_repo, ttl_seconds=4)
# Schemy FastAPI
class NoteIn(BaseModel):
    content: str  # zaszyfrowany lokalnie tekst


class NoteEdit(BaseModel):
    client_private_key_b64: str  # base64-encoded client private key used to decrypt existing package
    new_plaintext: str  # nowa treść (plaintext) którą zapiszemy i ponownie zaszyfrujemy


class NoteOut(BaseModel):
    id: int
    plaintext: str  # po odszyfrowaniu serwerowym (nadal zaszyfrowany lokalnie)  

@router.post("/")
async def create(note_in: NoteIn):
    '''wstaw notatke/i na server'''
    client_priv, client_pub = encryption_service.generate_nacl_keypair()#tworzy klucz klienta
    
    lokalny_pakiet_szyfrowany= encryption_service.encrypt_for_recipient(note_in.content,client_pub)
    lokalny_pakiet=lokalny_pakiet_szyfrowany.decode()
    
    note = await create_use_case.execute(lokalny_pakiet)
    
    return {
        "id": note.id, 
        "client_private_key": base64.b64encode(client_priv).decode(),
        "client_public_key": base64.b64encode(client_pub).decode(),
        "server encrypted": note.content.decode(),
        "local_encrypted": lokalny_pakiet,
        }


@router.get("/{note_id}")#pobierz konkretną notke
async def get(note_id: int,klucz_prywatny:str):
    '''pobieranie notatek'''
    # pobierz lokalnie zaszyfrowaną zawartość (serwer odszyfrował swoją warstwę)
    content = await get_use_case.execute(note_id)

    if content is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    bity_klucza_priv= base64.b64decode(klucz_prywatny)
    # klient odszyfrowuje pakiet hybrydowy
    try:
        text = encryption_service.decrypt_with_private(content.encode(),bity_klucza_priv)
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"odszyfrowanie nie powiodło się: {e}")
    
    return {
        "id": note_id,
        "plaintext": text
        }


@router.patch("/{note_id}")
async def update_note(note_id: int, edit: NoteEdit):
    """Edit flow:
    - Pobiera zapisany lokalny pakiet (po odszyfrowaniu serwerowym).
    - Próbuje odszyfrować go podanym `client_private_key_b64` aby zweryfikować prawo do edycji.
    - Jeśli klucz poprawny, bierze `new_plaintext`, wygeneruje nową parę NaCl,
      zaszyfruje `new_plaintext` lokalnie (hybrydowo) i zapisze wynik na serwerze (serwerowa warstwa Fernet).
    - Zwraca nowy prywatny klucz klienta (base64), publiczny klucz (base64) i nowy lokalny pakiet (str).
    - client_private_key_b64 - tutaj wstaw stary klucz prywatny z orginalnej notatki
    """
    # Pobierz aktualny lokalny pakiet
    local_pkg = await get_use_case.execute(note_id)
    if local_pkg is None or local_pkg == "None":
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")

    # Odszyfruj istniejący pakiet klienta przy użyciu podanego prywatnego klucza
    try:
        priv_bytes = base64.b64decode(edit.client_private_key_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid base64 for client_private_key_b64")

    try:
        _current_plain = encryption_service.decrypt_with_private(local_pkg.encode(), priv_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"client decryption failed: {e}")

    # Używamy new_plaintext jako treści do zapisania
    new_plaintext = edit.new_plaintext

    # Generujemy nową parę kluczy klienta i szyfrujemy plaintext lokalnie
    new_priv, new_pub = encryption_service.generate_nacl_keypair()
    new_local_package_bytes = encryption_service.encrypt_for_recipient(new_plaintext, new_pub)
    new_local_package = new_local_package_bytes.decode()

    # Zapisz: edit_use_case oczekuje lokalnego pakietu jako string
    updated_note = await edit_use_case.execute(note_id, new_local_package)
    if updated_note is None:
        raise HTTPException(status_code=500, detail="failed to update note")

    return {
        "id": note_id,
        "new_client_private_key_b64": base64.b64encode(new_priv).decode(),
        "new_client_public_key_b64": base64.b64encode(new_pub).decode(),
        "new_local_encrypted": new_local_package,
        "plaintext_saved": new_plaintext,
    }

@router.delete("/{note_id}")#usuń
async def delete_note(note_id:int):
    success=await delete_note_use_case.execute(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"message":"Notatka została usunięta"}

@router.get("/")#pobierz wszystko
async def get_all_notes():
    """Pobiera wszystkie notatki (tylko do celów testowych)"""
    all_notes = await note_repo.get_all()
    result = []
    if not all_notes:
        raise HTTPException(status_code=404)
    for note in all_notes:
        decrypted_content = await get_use_case.execute(note.id)

        result.append({"id": note.id, "content": decrypted_content})
    return result