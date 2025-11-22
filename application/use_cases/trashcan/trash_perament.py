from domain.interfaces import TrashRepository

class PermamentDelitionUseCase:
    def __init__(self,trash_can:TrashRepository):
        self._trash=trash_can
    async def execute(self,note_id:int)->bool:
        '''permamentne usuwanie'''
        result=await self._trash.delete_trashed_note_permanently(note_id)
        return result