from domain.interfaces import NoteRepository

class NoteDeleteUseCase:
    '''pobiera odkodowuje a następnie usuwa notatkę'''
    def __init__(self,repo:NoteRepository) :
        self.repo=repo
        
    async def execute(self,note_id:int)->bool:
        '''usuń notatkę o danym id udało się code: 1 else code:0'''
        return await self.repo.delete_notes(note_id)