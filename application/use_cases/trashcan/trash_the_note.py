from domain.entities import Note, trash
from domain.interfaces import NoteRepository, TrashRepository

class TrashNoteUseCase:
    def __init__(self, note_repo:NoteRepository,trash_can:TrashRepository) :
        '''konstruktor'''
        self.note_repo=note_repo
        self.trash_can=trash_can
    async def execute(self,note_id:int)->bool:
        '''usuń notatkę i przenieś ją do kosza'''
        note=await self.note_repo.get_note_by_id(note_id)
        if note:
            await self.trash_can.add_to_trash(note)
            await self.note_repo.delete_notes(note_id)
            return True
        return False