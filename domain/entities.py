from dataclasses import dataclass
from typing import Optional
@dataclass
class Note:
    id:int
    title: bytes
    content:bytes #dla lepszego bezpieczeństwa danych
    created_at: Optional[str] = None  # data w formacie 'dd-mm-yy'
    tags: Optional[str] = None
    key_private_b64: Optional[str] = None  # base64-encoded client private key

@dataclass
class Trash:
    id: int
    title: bytes
    content: bytes
    tags: Optional[str] = None
    created_at: Optional[str] = None  # data w formacie 'dd-mm-yy'
    trashed_at: Optional[str] = None  # data w formacie 'dd-mm-yy'
    key_private_b64: Optional[str] = None  # base64-encoded client private key