from domain.interfaces import TrashRepository
from application.services.encryption_service import EncryptionService
from uuid import UUID
from typing import Literal

class TrashGetterUseCase:
    def __init__(self,trash_can:TrashRepository,dencryption:EncryptionService):
        '''zobacz co usunołeś'''
        self._trash_can=trash_can
        self._encryption=dencryption
    
    async def execute(self,*,note_id:int,user_uuid:UUID,field:Literal["content","title"])->str|None:
        '''odszyfruj dla widoku '''
        trashed_note=await self._trash_can.get_by_id(note_id=note_id,user_uuid=user_uuid)
        

        if not trashed_note:
            return None
        
        encrypted_value=getattr(trashed_note,field,None)
        if encrypted_value is None:
            return None
        return self._encryption.decryptserver(encrypted_value)
    