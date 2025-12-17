from typing import List, Optional, cast
import base64

from domain.entities import Note, Trash
from domain.interfaces import NoteRepository, TrashRepository, SearchServiceInterface

from application.common.utils import tags_to_list
from application.services.search.search_dto import NotesSearchQuery
from application.services.encryption_service import EncryptionService


class SearchService(SearchServiceInterface):
    """Service for searching notes with loose matching.
    
    Performs case-insensitive, partial matching on:
    - Decrypted note titles
    - Decrypted note content
    - Note tags
    """

    def __init__(self,encryption_service: EncryptionService,note_repo: NoteRepository,trash_repo: TrashRepository):
        self.encryption = encryption_service
        self.note_repo = note_repo
        self.trash_repo = trash_repo

    async def _decrypt_title(self, title_bytes: Optional[bytes], key_private_b64: Optional[str], note_id: int) -> Optional[str]:
        """Decrypts note title using hybrid encryption.
        
        Returns None if decryption fails or required data is missing.
        """
        if not title_bytes or not key_private_b64:
            return None

        try:
            note = await self.note_repo.get_note_by_id(note_id)
            if note and note.title == title_bytes and note.key_private_b64 == key_private_b64:
                priv = base64.b64decode(cast(bytes, note.key_private_b64))
                title_dec = self.encryption.decrypt_server(title_bytes)
                priv_decrypt = self.encryption.decrypt_with_private(title_dec.encode(), priv)
                return priv_decrypt

            trash = await self.trash_repo.get_trashed_note_by_id(note_id)
            if trash and trash.title == title_bytes and trash.key_private_b64 == key_private_b64:
                priv = base64.b64decode(cast(bytes, trash.key_private_b64))
                trash_title_dec = self.encryption.decrypt_server(trash.title)
                priv_decrypt = self.encryption.decrypt_with_private(trash_title_dec.encode(), priv)
                return priv_decrypt
        except Exception:
            return None

        return None

    async def _decrypt_content(self, content_bytes: Optional[bytes], key_private_b64: Optional[str], note_id: int) -> Optional[str]:
        """Decrypts note content using hybrid encryption.
        
        Returns None if decryption fails or required data is missing.
        """
        if not content_bytes or not key_private_b64:
            return None

        try:
            note = await self.note_repo.get_note_by_id(note_id)
            if note and note.content == content_bytes and note.key_private_b64 == key_private_b64:
                priv = base64.b64decode(cast(bytes, note.key_private_b64))
                content_dec = self.encryption.decrypt_server(content_bytes)
                priv_decrypt = self.encryption.decrypt_with_private(content_dec.encode(), priv)
                return priv_decrypt

            trash = await self.trash_repo.get_trashed_note_by_id(note_id)
            if trash and trash.content == content_bytes and trash.key_private_b64 == key_private_b64:
                priv = base64.b64decode(cast(bytes, trash.key_private_b64))
                trash_content_dec = self.encryption.decrypt_server(trash.content)
                priv_decrypt = self.encryption.decrypt_with_private(trash_content_dec.encode(), priv)
                return priv_decrypt
        except Exception:
            return None

        return None

    def _matches_query(self, text: Optional[str], query: str) -> bool:
        """Checks if text contains query (case-insensitive, partial match).
        
        Returns True if query is found in text, False otherwise.
        """
        if not text:
            return False
        return query.lower() in text.lower()

    def _matches_tags(self, tags: Optional[str], query: str) -> bool:
        """Checks if any tag contains the query (case-insensitive, partial match).
        
        Returns True if query is found in any tag, False otherwise.
        """
        if not tags:
            return False
        tag_list = tags_to_list(tags)
        query_lower = query.lower()
        return any(query_lower in tag for tag in tag_list)

    async def _note_matches(self, note: Note, search_query: NotesSearchQuery) -> bool:
        """Checks if a note matches the search query.
        
        Searches in decrypted title, decrypted content, and tags.
        """
        query = search_query.query

        # Check tags (no decryption needed)
        if self._matches_tags(note.tags, query):
            return True

        # Check title (needs decryption)
        decrypted_title = await self._decrypt_title(note.title, note.key_private_b64, note.id)
        if decrypted_title and self._matches_query(decrypted_title, query):
            return True

        # Check content (needs decryption)
        decrypted_content = await self._decrypt_content(note.content, note.key_private_b64, note.id)
        if decrypted_content and self._matches_query(decrypted_content, query):
            return True

        return False

    async def search_notes(self, repo: NoteRepository, search_query: NotesSearchQuery) -> List[Note]:
        """Searches for notes matching the query.
        
        Returns a list of notes where the query appears in:
        - Title (decrypted)
        - Content (decrypted)
        - Tags
        """
        all_notes = await repo.get_all()
        matching_notes = []

        for note in all_notes:
            if await self._note_matches(note, search_query):
                matching_notes.append(note)

        return matching_notes

    async def search_trash(self, repo: TrashRepository, search_query: NotesSearchQuery) -> List[Trash]:
        """Searches for trashed notes matching the query.
        
        Returns a list of trashed notes where the query appears in:
        - Title (decrypted)
        - Content (decrypted)
        - Tags
        """
        all_trash = await repo.get_all_trashed()
        matching_trash = []

        for trash in all_trash:
            # Reuse similar logic but for Trash entity
            query = search_query.query

            # Check tags
            if self._matches_tags(trash.tags, query):
                matching_trash.append(trash)
                continue

            # Check title
            decrypted_title = await self._decrypt_title(trash.title, trash.key_private_b64, trash.id)
            if decrypted_title and self._matches_query(decrypted_title, query):
                matching_trash.append(trash)
                continue

            # Check content
            decrypted_content = await self._decrypt_content(trash.content, trash.key_private_b64, trash.id)
            if decrypted_content and self._matches_query(decrypted_content, query):
                matching_trash.append(trash)

        return matching_trash

