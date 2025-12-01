from typing import List, Optional
from domain.entities import Note, Trash
from domain.interfaces import TrashRepository


class InMemoryTrashRepository(TrashRepository):
    def __init__(self) -> None:
        '''in_memory storage dla kosza'''
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
        '''przywróć notatkę z kosza jako Note (usuń z kosza)'''
        restored = await self.get_trashed_note_by_id(note_id)
        if restored:
            self._trashed.remove(restored)
            note = Note(id=restored.id, content=restored.content, key_private_b64=restored.key_private_b64)
            return note
        return None

    async def delete_trashed_note_permanently(self, note_id: int) -> bool:
        '''permanentne usunięcie notatki z kosza'''
        trashed_note = await self.get_trashed_note_by_id(note_id)
        if trashed_note:
            self._trashed.remove(trashed_note)
            return True
        return False