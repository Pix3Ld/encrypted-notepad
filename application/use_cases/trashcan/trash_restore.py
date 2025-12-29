from domain.interfaces import NoteRepository,TrashRepository
from domain.entities import Note
from uuid import UUID
class TrashRestoreUseCase:
    def __init__(self,note:NoteRepository,trash:TrashRepository):
        '''przywraca note z kosza spowrotem do note_repo'''
        self._note=note
        self._trash=trash
    async def execute(self,*,note_id:int,user_uuid:UUID)->bool:
        '''przywraca notatkę z kosza do note_repo'''
        trashed = await self._trash.restore(
            note_id=note_id,
            user_uuid=user_uuid,
        )
        if not trashed:
            return False
        
        restored = Note(
            id=trashed.id,
            title=trashed.title,
            content=trashed.content,
            user_uuid=trashed.user_uuid,
            tags=trashed.tags,
            created_at=trashed.created_at,
            key_private_b64=trashed.key_private_b64,
            public_key_b64=trashed.public_key_b64,
        )
        await self._note.add(
            note=restored
        )
        await self._trash.delete_permanently(
            note_id=note_id,
            user_uuid=user_uuid
        )
        return True