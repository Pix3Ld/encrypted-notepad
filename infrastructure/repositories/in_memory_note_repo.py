from domain.entities import Note
from typing import List, Optional
from domain.interfaces import NoteRepository

class Get_Note_UseCase:
    def __init__(self) -> None:
        self._notes: List[Note] = []#in_memory storage dla naszych notatek (to jest za postgresa narazie)
        '''a tu jest pamięc naszej bazy danych in_memory'''
    def add(self,note:Note)->None: #to dodaje do in_memory storage
        '''dodaj do bazy(temp bazy) notatke'''
        self._notes.append(note)
    def get_by_id(self,note_id:int)->Optional[Note]: #to pobiera z in_memory storage
        '''zgarnia notke po id'''
        for note in self._notes:
            if note.id==note_id:
                return note
        return None
    def get_all(self)->List[Note]: #dawaj wszysko bo gruby jest głodny
        '''daje wszystkie informacje z bazy dosłownie wszystkie'''
        return self._notes