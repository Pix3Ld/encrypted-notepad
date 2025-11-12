from dataclasses import dataclass
@dataclass
class Note:
    id:int
    content:bytes #dla lepszego bezpieczeństwa danych 