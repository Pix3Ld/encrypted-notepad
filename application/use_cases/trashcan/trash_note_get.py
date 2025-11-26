from domain.interfaces import TrashRepository
from application.services.encryption_service import EncryptionService

class TrashGetterUseCase:
    def __init__(self,trash_can:TrashRepository,dencryption:EncryptionService):
        '''zobacz co usunołeś'''
        self._trash_can=trash_can
        self._encryption=dencryption
    
    async def execute(self,note_id:int)->str:
        '''odszyfruj dla widoku '''
        trashed_note=await self._trash_can.get_trashed_note_by_id(note_id)
        if not trashed_note:
            return "None"
        return self._encryption.decryptserver(trashed_note.content)