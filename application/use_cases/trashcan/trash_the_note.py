from domain.entities import Note, Trash
import time
from domain.interfaces import NoteRepository, TrashRepository


class TrashNoteUseCase:

    def __init__(self, note_repo: NoteRepository, trash_repo: TrashRepository):
        '''przenieś note do kosza'''
        self.note_repo = note_repo
        self.trash_repo = trash_repo

    async def execute(self, note_id: int) -> bool:
        '''usuń notatkę z note_repo i przenieś ją do trash_repo'''
        note = await self.note_repo.get_note_by_id(note_id)
        if note:
            trashed = Trash(id=note.id, content=note.content, trashed_at=time.time())
            await self.trash_repo.add_to_trash(trashed)
            await self.note_repo.delete_notes(note_id)
            return True
        return False