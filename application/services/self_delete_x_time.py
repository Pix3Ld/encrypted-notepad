from domain.interfaces import TrashRepository
from typing import Optional
from datetime import datetime

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

        trashed_at: Optional[str] = getattr(trashed, "trashed_at", None)  # data przeniesienia do kosza w formacie 'dd-mm-yy'
        if trashed_at is None:
            return False

        # Konwersja 'dd-mm-yy' na datę i porównanie z TTL (dni -> sekundy).
        try:
            t_dt = datetime.strptime(trashed_at, "%d-%m-%y")
        except Exception:
            return False
        # ttl_seconds interpretujemy nadal jako sekundy – dodajemy do daty (początek dnia) offset sekund.
        epoch_seconds = t_dt.timestamp()
        now_seconds = datetime.now().timestamp()
        if now_seconds >= epoch_seconds + self._ttl:
            return await self._trash.delete_trashed_note_permanently(note_id)

        return False

    async def execute_all(self) -> int:
        """Automatycznie usuwa wszystkie notatki w koszu, które przekroczyły czas życia (TTL).
        
        Returns:
            Liczba trwale usuniętych notatek
        """
        all_trashed = await self._trash.get_all_trashed()
        deleted_count = 0
        now_seconds = datetime.now().timestamp()

        for trashed in all_trashed:
            trashed_at: Optional[str] = getattr(trashed, "trashed_at", None)
            if trashed_at is None:
                continue

            try:
                t_dt = datetime.strptime(trashed_at, "%d-%m-%y")
                epoch_seconds = t_dt.timestamp()
                if now_seconds >= epoch_seconds + self._ttl:
                    if await self._trash.delete_trashed_note_permanently(trashed.id):
                        deleted_count += 1
            except Exception:
                continue

        return deleted_count