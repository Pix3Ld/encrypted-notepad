import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from application.use_cases.create_note import CreateNoteUseCase
from application.use_cases.get_note import GetNoteUseCase
from application.use_cases.edit_note import EditNoteUseCase


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

# Trash use cases
trash_note_use_case = TrashNoteUseCase(note_repo, trash_repo)
trash_getter_use_case = TrashGetterUseCase(trash_repo, encryption_service)
trash_restore_use_case = TrashRestoreUseCase(note_repo, trash_repo)
permament_delete_use_case = PermamentDelitionUseCase(trash_repo)
self_delete_service = Delete_X_Time(trash_repo, ttl_seconds=4)
# Schemy FastAPI
class NoteIn(BaseModel):
    title: str
    content: str  # zaszyfrowany lokalnie tekst
    tags: Optional[str]=None


class NoteEdit(BaseModel):
    new_plaintext: str  # nowa treść (plaintext) którą zapiszemy i ponownie zaszyfrujemy


@router.post("/")
async def create(note_in: NoteIn):
    ''' tworzy notatkę:
    - generuje parę kluczy NaCl (prywatny i publiczny) dla klienta
    - szyfruje zawartość notatki lokalnie (hybrydowo) przy użyciu klucza publicznego klienta
    - przekazuje zaszyfrowaną zawartość do CreateNoteUseCase wraz z kluczem prywatnym klienta (base64)
    - zwraca ID notatki, klucz prywatny klienta (base64), klucz publiczny klienta (base64), zaszyfrowaną zawartość serwera i lokalnie
    
    '''
    client_priv, client_pub = encryption_service.generate_nacl_keypair()  # tworzy klucz klienta
    client_priv_b64 = base64.b64encode(client_priv).decode()
    
    lokalny_pakiet_szyfrowany= encryption_service.encrypt_for_recipient(note_in.content,client_pub)
    lokalny_title_szyfrowany=encryption_service.encrypt_for_recipient(note_in.title,client_pub)
    lokalny_pakiet=lokalny_pakiet_szyfrowany.decode()
    lokalny_title=lokalny_title_szyfrowany.decode()
    
    # Pass private key to use case so it gets stored in the note
    note = await create_use_case.execute(lokalny_pakiet, client_private_key_b64=client_priv_b64, title=lokalny_title,tags=note_in.tags)
    
    return {
        "id": note.id, 
        "client_private_key": client_priv_b64,
        "client_public_key": base64.b64encode(client_pub).decode(),
        "server encrypted": note.content.decode(),
        "title":note.title.decode(),
        "tags":note.tags,
        "local_encrypted": lokalny_pakiet,
        }


@router.get("/{note_id}")#pobierz konkretną notke
async def get(note_id: int,klucz_prywatny:str):
    '''pobieranie notatek dla wskazanego ID:
    - Pobiera zaszyfrowaną lokalnie zawartość notatki (po odszyfrowaniu serwerowym).
    - Odszyfrowuje lokalny pakiet przy użyciu podanego `klucz_prywatny` (base64).
    - Zwraca ID notatki i odszyfrowany tekst (content).
    '''
    # pobierz lokalnie zaszyfrowaną zawartość (serwer odszyfrował swoją warstwę)
    content = await get_use_case.execute(note_id)
    title = await get_use_case.title_execute(note_id)
    tag = await note_repo.get_note_by_id(note_id)

    if content is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    bity_klucza_priv= base64.b64decode(klucz_prywatny)
    # klient odszyfrowuje pakiet hybrydowy
    try:
        text = encryption_service.decrypt_with_private(content.encode(),bity_klucza_priv)
        file_name = encryption_service.decrypt_with_private(title.encode(),bity_klucza_priv)
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"odszyfrowanie nie powiodło się: {e}")
    
    return {
        "id": note_id,
        "content": text,
        "title": file_name,
        "tags": tag.tags if tag is not None else None,
        }


@router.patch("/{note_id}")
async def update_note(note_id: int, edit: NoteEdit,key_priv:str,new_title: str |None=None ,new_tags: str |None=None): #wywalenie optional z tag u tytułu
    """Edit flow:
    - Pobiera zapisany lokalny pakiet (po odszyfrowaniu serwerowym).
    - Próbuje odszyfrować go podanym `client_private_key_b64` aby zweryfikować prawo do edycji.
    - Jeśli klucz poprawny, bierze `new_plaintext`, wygeneruje nową parę NaCl,
      zaszyfruje `new_plaintext` lokalnie (hybrydowo) i zapisze wynik na serwerze (serwerowa warstwa Fernet).
    - Zwraca nowy prywatny klucz klienta (base64), publiczny klucz (base64) i nowy lokalny pakiet (str).
    - client_private_key_b64 - tutaj wstaw stary klucz prywatny z orginalnej notatki
    """
    #błąd jest w tym że pakiety nie pobierają starych wartośći np string lub bytes(title) tylko to co jest w pamięci egs <corutine.....>
    #kurwa jak zmienić 
    
    # Pobierz aktualny lokalny pakiet

    old_tags= await note_repo.get_note_by_id(note_id)
    local_pkg = await get_use_case.execute(note_id)
    title_pkg = await get_use_case.title_execute(note_id)
    
    if local_pkg is None or local_pkg == "None":
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")

    # Odszyfruj istniejący pakiet klienta przy użyciu podanego prywatnego klucza
    try:
        priv_bytes = base64.b64decode(key_priv)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid base64 for client_private_key_b64")
    try:
        _current_plain = encryption_service.decrypt_with_private(local_pkg.encode(), priv_bytes)
        title_plain= encryption_service.decrypt_with_private(title_pkg.encode(), priv_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"tutaj się coś psuje: {e}")

    # Używamy new_plaintext jako treści do zapisania
    new_plaintext = edit.new_plaintext
    replace_title=new_title if new_title is not None else title_plain
    new_tag=new_tags if new_tags is not None else old_tags.tags if old_tags is not None else None

    # Generujemy nową parę kluczy klienta i szyfrujemy plaintext lokalnie
    new_priv, new_pub = encryption_service.generate_nacl_keypair()
    new_priv_b64 = base64.b64encode(new_priv).decode()

    new_local_package_bytes = encryption_service.encrypt_for_recipient(new_plaintext, new_pub)
    new_local_package = new_local_package_bytes.decode()

    new_local_title_bytes = encryption_service.encrypt_for_recipient(replace_title,new_pub)
    new_local_title = new_local_title_bytes.decode()

    # Zapisz: edit_use_case oczekuje lokalnego pakietu jako string i nowego klucza
    updated_note = await edit_use_case.execute(
        note_id,
        new_local_package,
        new_client_private_key_b64=new_priv_b64,
        new_title=new_local_title,
        new_tags=new_tag)
    if updated_note is None:
        raise HTTPException(status_code=500, detail="failed to update note")

    return {
        "id": note_id,
        "new_client_private_key_b64": new_priv_b64,
        "new_client_public_key_b64": base64.b64encode(new_pub).decode(),
        "new_local_encrypted": new_local_package,
        "plaintext_saved": new_plaintext,
        "new_title":replace_title,
        "tags":new_tag,
    }


@router.get("/")#pobierz wszystko
async def get_all_notes():
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

        prive_key=base64.b64decode(note.key_private_b64) if note.key_private_b64 else None

        try:

            decrypted_content = encryption_service.decrypt_with_private(decrypted_content.encode(), prive_key) if prive_key else "No private key stored"  
            decrypt_title = encryption_service.decrypt_with_private(decrypt_title.encode(), prive_key) if prive_key else "No private key stored"   

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło {e}")
        
        result.append(
            {
            "id": note.id,
            "title": decrypt_title,
            "content": decrypted_content,
            "tags":note.tags,
            "private_key": note.key_private_b64,
            }
            )
    return result
@router.delete("/{note_id}")#usuń
async def delete_note(note_id:int):
    '''przenosi notatkę do kosza
    - usuwa notatkę z repozytorium notatek
    - dodaje notatkę do repozytorium kosza z aktualnym timestampem
    '''
    success = await trash_note_use_case.execute(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"message":"Notatka została przeniesiona do kosza"}

@router.get("/trash/")
async def get_trashed_notes():
    '''pobiera notatki znajdujące się w koszu
    - pobiera wszystkie notatki z repozytorium kosza
    - dla każdej notatki odszyfrowuje lokalny pakiet przy użyciu przechowywanego klucza prywatnego (jeśli dostępny)
    - zwraca listę notatek z ich ID, odszyfrowaną zawartością, czasem przeniesienia do kosza i kluczem prywatnym (base64)
    '''
    trashed = await trash_repo.get_all_trashed()
    result = []
    for note in trashed:
        decrypted = await trash_getter_use_case.execute(note.id)
        privkey=base64.b64decode(note.key_private_b64) if note.key_private_b64 else None
        try:
            decrypt= encryption_service.decrypt_with_private(decrypted.encode(),privkey) if privkey else "nie ma klucza prywatnego"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"odszyfrowanie nie powiodło się: {e}")
        result.append({
            "id": note.id,
            "content": decrypt,
            "trashed_at": note.trashed_at,
            "private_key": note.key_private_b64
        })
    return result

@router.post("/trash/restore/{note_id}")
async def restore_trashed(note_id:int):
    '''przywraca z kosza do notes
    - usuwa notatkę z repozytorium kosza
    - dodaje notatkę z powrotem do repozytorium notatek wraz z oryginalnymi danymi czyli kluczami i zawartością
    '''
    to_restore = await trash_restore_use_case.execute(note_id)
    if to_restore is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu")
    return "Notatka została przywrócona z kosza"

@router.delete("/trash/permanent/{note_id}")
async def permament_deletion(note_id:int):
    '''manualne permamentne usuwanie z kosza'''
    result = await permament_delete_use_case.execute(note_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu")
    return "usunięto na stałe(a to długi okres czasu)"

@router.delete("/trash/after_time/{note_id}")
async def auto_delete(id_note:int):
    '''testowanie automatycznego usuwania 
    - sprawdza czy notatka o podanym ID istnieje w koszu i czy minął czas TTL(data ważności)
    - jeśli tak, usuwa notatkę na stałe z repozytorium kosza
    - zwraca komunikat o sukcesie lub błąd 404 jeśli notatka nie istnieje lub czas nie minął
    '''
    to_perma= await self_delete_service.execute(id_note)
    if not to_perma:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje w koszu lub czas nie minął")
    return "notatka usunięta autoamtycznie"