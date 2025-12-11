from typing import List, Optional
import base64

from domain.entities import Note, Trash
from domain.interfaces import NoteRepository, TrashRepository

from application.common.utils import parse_created_at_str,tags_to_list
from application.services.filtering.filter_dto import NotesFilter
from application.services.encryption_service import EncryptionService
from typing import cast

class FilteringService:
    def __init__(self, encryption_service:EncryptionService,note_repo:NoteRepository,trash_repo:TrashRepository):
        self.encryption = encryption_service
        self.note=note_repo
        self.trash=trash_repo

    async def _decrypt_title(self, title_bytes: Optional[bytes], key_private_b64: Optional[str],id:int) -> Optional[str]:
        nota = await self.note.get_note_by_id(id)
        trash = await self.trash.get_trashed_note_by_id(id)
        if nota is not None:
            print("DEBUG: brak title_bytes lub key_private_b64")
            if nota.title==title_bytes:
                print("tytuły się nie zgadzają")
                if nota.key_private_b64 == key_private_b64:
                    print("DEBUG: brak key_private_b64 albo się nie zgadzają")
                    priv=base64.b64decode(cast(bytes,nota.key_private_b64))
                    title_dec=self.encryption.decryptserver(nota.title)
                    priv_decrypt = self.encryption.decrypt_with_private(title_dec.encode(),priv)
                    return priv_decrypt 
              
        if trash is not None:
            if trash.title==title_bytes:
               if trash.key_private_b64==key_private_b64:
                   priv=base64.b64decode(cast(bytes,trash.key_private_b64))
                   trash_title_dec=self.encryption.decrypt_server(trash.title)
                   priv_decrypt = self.encryption.decrypt_with_private(trash_title_dec.encode(),priv)
                   return priv_decrypt
           
        if not title_bytes or not key_private_b64:
            print("DEBUG: brak title_bytes lub key_private_b64")
            return None

    async def _match_by_title(self, title_bytes, key_private_b64: Optional[str], f: NotesFilter,id:int) -> bool:
        if not f.title:
            return True
        decrypted = await self._decrypt_title(title_bytes, key_private_b64,id)
        if decrypted is None:
            return False
        return f.title == decrypted

    async def _match_by_tag(self, tags, f: NotesFilter) -> bool:
        if not f.tag:
            return True
        return f.tag.lower() in tags_to_list(tags)

    async def _match_by_date(self, created_at_str, f: NotesFilter) -> bool:
        if not (f.date_eq or f.date_from or f.date_to):
            return True

        created = parse_created_at_str(created_at_str)
        if created is None:
            return False

        if f.date_eq and created != f.date_eq:
            return False
        if f.date_from and created < f.date_from:
            return False
        if f.date_to and created > f.date_to:
            return False

        return True

    async def _match_note(self, note: Note, f: NotesFilter,id:int) -> bool:
        return (
            await self._match_by_title(note.title, note.key_private_b64, f,id) and
            await self._match_by_tag(note.tags, f) and
            await self._match_by_date(note.created_at, f)
        )

    async def _match_trash(self, trash: Trash, f: NotesFilter,id:int) -> bool:
        return (
            await self._match_by_title(trash.title, trash.key_private_b64, f,id) and
            await self._match_by_tag(trash.tags, f) and
            await self._match_by_date(trash.created_at, f)
        )

    async def filter_notes(self, repo: NoteRepository, filters: NotesFilter) -> List[Note]:
        return [n for n in await repo.get_all() if self._match_note(n, filters,n.id)]

    async def filter_trash(self, repo: TrashRepository, filters: NotesFilter) -> List[Trash]:
        return [t for t in await repo.get_all_trashed() if self._match_trash(t, filters,t.id)]
