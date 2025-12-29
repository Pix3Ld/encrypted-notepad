from domain.interfaces import TrashRepository
from uuid import UUID
class PermamentDelitionUseCase:
    def __init__(self,trash_can:TrashRepository):
        '''zapewnia permamentne usuwanie notatki z kosza'''
        self._trash=trash_can
    async def execute(self,*,note_id:int,user_uuid:UUID)->bool:
        '''permamentne usuwanie'''
        result=await self._trash.delete_permanently(note_id=note_id,user_uuid=user_uuid)
        return result