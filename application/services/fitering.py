from __future__ import annotations

from typing import List, Optional
from datetime import datetime, date

from pydantic import BaseModel, validator

from domain.entities import Note, Trash
from domain.interfaces import NoteRepository, TrashRepository


DATE_FMT = "%d-%m-%y"  # dd-mm-yy


def _safe_decode_title(title_bytes: Optional[bytes]) -> str:
    if title_bytes is None:
        return ""
    try:
        return title_bytes.decode("utf-8", errors="ignore")
    except Exception:
        # fallback: bytes repr aby filtr się nie wysypał
        return str(title_bytes)


def _parse_created_at_str(cration_date: Optional[str]) -> Optional[date]:
    if not cration_date:
        return None
    try:
        return datetime.strptime(cration_date, DATE_FMT).date()
    except Exception:
        return None


def _tags_to_list(tags: Optional[str]) -> List[str]:
    if not tags:
        return []
    # czyszczenie tagów
    raw = [p.strip() for part in tags.replace(";", ",").split(";") for p in part.split(",")]
    out: List[str] = []
    for item in raw:
        if not item:
            continue
        out.extend([t for t in item.split() if t])
    return [t.lower() for t in out]


class NotesFilter(BaseModel):
    """Filtruj DTO pod kątem notatek i kosza.

    - title: dopasowanie capslock bez uwzględniania wielkości liter w zdekodowanych bajtach tytułu
    - tag: dopasowanie bez uwzględniania wielkości liter do dowolnego tokenu tagu (rozdzielonego przecinkiem/średnikiem/spacją)
    - date_eq: dopasowanie dokładnej daty utworzenia
    - date_from/date_to: dopasowanie zakresu włącznie dla daty utworzenia
    """

    title: Optional[str] = None
    tag: Optional[str] = None

    date_eq: Optional[date] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    # akceptuj string w  dd-mm-yy parsnij na date
    @validator("date_eq", "date_from", "date_to", pre=True)
    def _coerce_date(cls, valid):  # type: ignore[override]
        if valid is None or isinstance(valid, date):
            return valid
        if isinstance(valid, str) and valid.strip():
            try:
                return datetime.strptime(valid.strip(), DATE_FMT).date()
            except Exception:
                raise ValueError(f"Invalid date format. Expected {DATE_FMT}")
        return None

    class Config:
        anystr_strip_whitespace = True
        validate_assignment = True


class FilteringService:
    """Service do filtorwania Notes i Trash używając repo.

    logika filtrowania jest czysto in-memory i nie destruktywna.
    """

    def _match_by_title(self, title_bytes: Optional[bytes], f: NotesFilter) -> bool:
        if not f.title:
            return True
        title = _safe_decode_title(title_bytes).lower()
        return f.title.lower() in title

    def _match_by_tag(self, tags: Optional[str], f: NotesFilter) -> bool:
        if not f.tag:
            return True
        tag_tokens = _tags_to_list(tags)
        return f.tag.lower() in tag_tokens

    def _match_by_date(self, created_at_str: Optional[str], f: NotesFilter) -> bool:
        if not (f.date_eq or f.date_from or f.date_to):
            return True
        created = _parse_created_at_str(created_at_str)
        if created is None:
            return False
        if f.date_eq and created != f.date_eq:
            return False
        if f.date_from and created < f.date_from:
            return False
        if f.date_to and created > f.date_to:
            return False
        return True

    def _match_note(self, note: Note, f: NotesFilter) -> bool:
        return (
            self._match_by_title(note.title, f)
            and self._match_by_tag(note.tags, f)
            and self._match_by_date(note.created_at, f)
        )

    def _match_trash(self, trash: Trash, f: NotesFilter) -> bool:
        # As requested: filter by created_at, title and tag (not trashed_at)
        return (
            self._match_by_title(trash.title, f)
            and self._match_by_tag(trash.tags, f)
            and self._match_by_date(trash.created_at, f)
        )

    async def filter_notes(self, repo: NoteRepository, filters: NotesFilter) -> List[Note]:
        notes = await repo.get_all()
        return [n for n in notes if self._match_note(n, filters)]

    async def filter_trash(self, repo: TrashRepository, filters: NotesFilter) -> List[Trash]:
        trashed = await repo.get_all_trashed()
        return [t for t in trashed if self._match_trash(t, filters)]


__all__ = ["NotesFilter", "FilteringService"]
