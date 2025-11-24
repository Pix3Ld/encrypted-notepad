from dataclasses import dataclass
from typing import Optional
@dataclass
class Note:
    id:int
    content:bytes #dla lepszego bezpieczeństwa danych 

@dataclass
class Trash:
    """Reprezentuje notatkę w koszu ze znacznikiem czasu wrzucenia.

    `trashed_at` to timestamp (float) zwracany przez `time.time()` w momencie przeniesienia do kosza.
    """
    id: int
    content: bytes
    trashed_at: Optional[float] = None