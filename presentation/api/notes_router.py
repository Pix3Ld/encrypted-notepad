from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from application.use_cases.create_note import CreateNoteUseCase
from application.use_cases.get_note import GetNoteUseCase
from application.use_cases.edit_note import EditNoteUseCase
from application.use_cases.delete_note import NoteDeleteUseCase

from application.services.encryption_service import EncryptionService
from infrastructure.repositories.in_memory_note_repo import InMemoryNoteRepository
from infrastructure.config.settings import settings

router=APIRouter(prefix="/notes",tags=["notes"])

#dependesy init
repo=InMemoryNoteRepository()
encryption_service = EncryptionService(settings.SERVER_KEY)
create_use_case = CreateNoteUseCase(repo, encryption_service)
get_use_case = GetNoteUseCase(repo, encryption_service)
edit_use_case = EditNoteUseCase(repo,encryption_service)
delete_note_use_case=NoteDeleteUseCase(repo)
# Schemy FastAPI
class NoteIn(BaseModel):
    content: str  # zaszyfrowany lokalnie tekst

class NoteOut(BaseModel):
    id: int
    content: str  # po odszyfrowaniu serwerowym (nadal zaszyfrowany lokalnie)

@router.post("/", response_model=NoteOut)
async def create(note_in: NoteIn):
    '''wstaw notatke/i na server'''
    note = await create_use_case.execute(note_in.content)
    return {"id": note.id, "content": note.content.decode()}

@router.get("/{note_id}", response_model=NoteOut)
async def get(note_id: int):
    '''pobieranie notatek'''
    content = await get_use_case.execute(note_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"id": note_id, "content": content}

@router.put("/{note_id}",response_model=NoteOut)
async def update_note(note_id:int, note_in:NoteIn):
    '''async edit endpoint'''
    update_content= await edit_use_case.execute(note_id,note_in.content)
    if update_content is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"id": note_id, "content": update_content}

@router.delete("/{note_id}")
async def delete_note(note_id:int):
    success=await delete_note_use_case.execute(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"message":"Notatka została usunięta"}

@router.get("/", response_model=list[NoteOut])
async def get_all_notes():
    """Pobiera wszystkie notatki (tylko do celów testowych)"""
    all_notes = await repo.get_all()
    result = []
    for note in all_notes:
        decrypted_content = await get_use_case.execute(note.id)
        result.append({"id": note.id, "content": decrypted_content})
    return result