from dataclasses import dataclass
from typing import Optional
@dataclass
class Note:
    id:int
    content:bytes #dla lepszego bezpieczeństwa danych
    key_private_b64: Optional[str] = None  # base64-encoded client private key 

@dataclass
class Trash:
    id: int
    content: bytes
    trashed_at: Optional[float] = None
    key_private_b64: Optional[str] = None  # base64-encoded client private key