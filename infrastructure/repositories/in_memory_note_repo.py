from typing import List, Optional
from domain.entities import Note
from domain.interfaces import NoteRepository

class InMemoryNoteRepository(NoteRepository):
    def __init__(self):
        self._notes = []#in_memory storage dla naszych notatek (to jest za postgresa narazie)
        '''a tu jest pamięc naszej bazy danych in_memory'''
    def add_note(self, note: Note) -> None: #to dodaje do in_memory storage
        self._notes.append(note)
        '''dodaj do bazy(temp bazy) notatke'''
    def get_note_by_id(self, note_id: int) -> Optional[Note]: #to pobiera z in_memory storage
        return next((n for n in self._notes if n.id == note_id), None)
        '''pobiera notatke z bazy else nic'''
    def get_all(self) -> List[Note]: #gimme all 
        return self._notes
        '''daje wszystkie informacje z bazy dosłownie wszystkie'''