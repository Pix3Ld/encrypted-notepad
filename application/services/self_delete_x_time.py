from domain.interfaces import TrashRepository
from typing import Optional
import time

''' 
na potem:
    - jak zrobisz bazę na dokerze to dodaj tam cron który będzie wykonywał ten skrypt co x(30 dni) czasu
    - prawdopodobnie będzie trzeba go doinstalować do obrazu
'''
class Delete_X_Time:
    """serwis do permanentnego usuwania notatek z kosza po określonym czasie.

    jak działa:
    - przy inicjalizacji przyjmuje repozytorium kosza i czas życia (ttl) w sekundach (domyślnie 4 sekundy dla testów)
    - metoda execute(note_id) sprawdza czy notatka o podanym ID znajduje się w koszu
      oraz czy minął czas życia od momentu przeniesienia do kosza (trashed_at + ttl)
    - jeśli tak, usuwa notatkę permanentnie z kosza 
    """

    def __init__(self, trashcan: TrashRepository, ttl_seconds: int = 4):
        self._trash = trashcan
        self._ttl = ttl_seconds

    async def execute(self, note_id: int) -> bool:
        """return true jeśli usunięto trwale

        funkcja sprawdza czy notatka w koszu przekroczyła czas życia (ttl).
        jeśli tak, usuwa ją permanentnie i zwraca True.
        """
        trashed = await self._trash.get_trashed_note_by_id(note_id)
        if trashed is None:
            return False

        trashed_at: Optional[float] = getattr(trashed, "trashed_at", None)# pobierz czas przeniesienia do kosza o ile istnieje
        if trashed_at is None:
            return False

        if time.time() >= trashed_at + self._ttl:
            return await self._trash.delete_trashed_note_permanently(note_id)

        return False