from typing import List, Optional
from domain.entities import Note, Trash
from domain.interfaces import NoteRepository, TrashRepository

class InMemoryNoteRepository(NoteRepository):
    def __init__(self):
        '''a tu jest pamięc naszej bazy danych in_memory'''
        self._notes = []#in_memory storage dla naszych notatek (to jest za postgresa narazie)

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
    
class InMemoryTrashRepository(TrashRepository,InMemoryNoteRepository):
    def __init__(self) -> None:
        '''in_memory storage dla kosza'''
        # initialize parent storage for notes
        InMemoryNoteRepository.__init__(self)
        self._trashed: List[Trash] = []
    async def add_to_trash(self, trashed_note: Trash) -> None:
        '''dodaj do kosza (przechowujemy obiekt Trash zawierający trashed_at)'''
        self._trashed.append(trashed_note)

    async def get_trashed_note_by_id(self, note_id: int) -> Optional[Trash]:
        '''pobiera notatkę z kosza po id''' 
        return next((n for n in self._trashed if n.id == note_id), None)

    async def get_all_trashed(self) -> List[Trash]:
        '''zwróć wszystkie notatki w koszu'''
        return self._trashed

    async def restore_note_from_trash(self, note_id: int) -> Optional[Note]:
        '''przywróć notatkę z kosza jako Note (usuń z kosza, dodaj do _notes)'''
        restored = await self.get_trashed_note_by_id(note_id)
        if restored:
            self._trashed.remove(restored)
            note = Note(id=restored.id, content=restored.content)
            self._notes.append(note)
            return note
        return None

    async def delete_trashed_note_permanently(self, note_id: int) -> bool:
        '''permanentne usunięcie notatki z kosza'''
        trashed_note = await self.get_trashed_note_by_id(note_id)
        if trashed_note:
            self._trashed.remove(trashed_note)
            return True
        return False