from typing import List, Optional
from domain.entities import Note
from domain.interfaces import NoteRepository

class InMemoryNoteRepository(NoteRepository):
    def __init__(self):
        '''a tu jest pamięc naszej bazy danych in_memory'''
        self._notes: List[Note]=[]#in_memory storage dla naszych notatek (to jest za postgresa narazie)

    async def add_note(self, note: Note) -> None: #to dodaje do in_memory storage
        '''dodaj do bazy(temp bazy) notatke'''
        self._notes.append(note)

    async def get_note_by_id(self, note_id: int) -> Optional[Note]: #to pobiera z in_memory storage
        '''pobiera notatke z bazy else nic'''
        return next((n for n in self._notes if n.id == note_id), None)
    
    async def get_all(self) -> List[Note]: #gimme all 
        '''daje wszystkie informacje z bazy dosłownie wszystkie'''
        return self._notes
    
    async def update_notes(self, note_id: int, new_content: bytes) ->Optional[Note]:
        note = await self.get_note_by_id(note_id)
        if note:
            note.content=new_content
            return note
        return None
    
    async def delete_notes(self, note_id: int) -> bool:
        note=await self.get_note_by_id(note_id)
        if note:
            self._notes.remove(note)
            return True
        return False