from domain.entities import Note
from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService
from typing import Optional
from datetime import datetime

class CreateNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        '''konstruktor do inicjalizacji repozytorium i serwisu szyfrującego'''
        '''repozytorium aka baza danych'''
        self.repo = repo
        self.encryption = encryption
    
    async def execute(self, local_encrypted_content: str,title:str, client_private_key_b64: Optional[str] = None,tags: Optional[str] = None) -> Note:
        '''wykorzystuje encryption service do ponownego zaszyfrowania notatki.
        wysłanej z klienta i zapisuje ją w repozytorium. Przechowuje też klucz prywatny klienta.'''
        encrypted_for_server = self.encryption.encryptserver(local_encrypted_content)
        encrypted_title = self.encryption.encryptserver(title)
        all_notes = await self.repo.get_all()
        note = Note(
            id=len(all_notes) + 1,
            title=encrypted_title,
            tags=tags,
            created_at=datetime.now().strftime("%d-%m-%y"),
            content=encrypted_for_server,
            key_private_b64=client_private_key_b64,
        )
        await self.repo.add_note(note)
        return note
        