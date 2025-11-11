from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from application.use_cases.create_note import CreateNoteUseCase
from application.use_cases.get_note import GetNoteUseCase
from application.services.encryption_service import EncryptionService
from infrastructure.repositories.in_memory_note_repo import InMemoryNoteRepository
from infrastructure.config.settings import settings

router=APIRouter(prefix="/notes",tags=["notes"])

#dependesy init
repo=InMemoryNoteRepository()
encryption_service = EncryptionService(settings.SERVER_KEY)
create_use_case = CreateNoteUseCase(repo, encryption_service)
get_use_case = GetNoteUseCase(repo, encryption_service)
# Schemy FastAPI
class NoteIn(BaseModel):
    content: str  # zaszyfrowany lokalnie tekst

class NoteOut(BaseModel):
    id: int
    content: str  # po odszyfrowaniu serwerowym (nadal zaszyfrowany lokalnie)

@router.post("/", response_model=NoteOut)
def create(note_in: NoteIn):
    note = create_use_case.execute(note_in.content)
    return {"id": note.id, "content": note.content.decode()}

@router.get("/{note_id}", response_model=NoteOut)
def get(note_id: int):
    content = get_use_case.execute(note_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Notatka nie istnieje")
    return {"id": note_id, "content": content}