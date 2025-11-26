from dataclasses import dataclass
from typing import Optional
@dataclass
class Note:
    id:int
    content:bytes #dla lepszego bezpieczeństwa danych 

@dataclass
class Trash:
    id: int
    content: bytes
    trashed_at: Optional[float] = None