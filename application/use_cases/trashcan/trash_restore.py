from domain.interfaces import NoteRepository,TrashRepository

class TrashRestoreUseCase:
    def __init__(self,note:NoteRepository,trash:TrashRepository):
        '''przywraca note z kosza spowrotem do note_repo'''
        self._note=note
        self._trash=trash
    async def execute(self,note_id:int)->bool:
        '''przywraca notatkę z kosza do note_repo'''
        trashed_note= await self._trash.restore_note_from_trash(note_id)
        if trashed_note:
            await self._note.add_note(trashed_note)
            await self._trash.delete_trashed_note_permanently(note_id)
            return True
        return False