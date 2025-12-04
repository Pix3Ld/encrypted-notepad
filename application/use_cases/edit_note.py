from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService
from typing import Optional
import time

class EditNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        self.repo = repo
        self.encryption = encryption

    async def execute(self, note_id: int, new_local_encrypted_content: str, new_client_private_key_b64: Optional[str]=None ,new_title:str | None=None, new_tags:str| None=None) -> str:
        '''Edytuje istniejącą notatkę o podanym ID, aktualizując jej zawartość i klucz prywatny.'''                         # zmieniłem z optional na stały zobaczmy co się stanie 
        existing_note = await self.repo.get_note_by_id(note_id)
        if not existing_note:
            return "nie ma notatki"
        
        encrypted_content = self.encryption.encryptserver(new_local_encrypted_content)
        new_encrypted_title =  self.encryption.encryptserver(new_title) if new_title is not None else existing_note.title # zamienia title na nowy zaszyfrowany title o ile jest podany 
        # Update the note with new encrypted content and potentially new private key
        existing_note.content = encrypted_content
        if new_client_private_key_b64:
            existing_note.key_private_b64 = new_client_private_key_b64

        if new_title is not None:
            existing_note.title = new_encrypted_title

        if new_tags is not None:
            existing_note.tags=new_tags

        if existing_note.created_at is not None:
            existing_note.created_at = time.time()
        
        
        updated_note = await self.repo.update_notes(note_id, encrypted_content,existing_note.title,existing_note.tags,existing_note.created_at)
        
        if updated_note:
            # Also update the key if provided
            if new_client_private_key_b64:
                updated_note.key_private_b64 = new_client_private_key_b64
            return self.encryption.decryptserver(updated_note.content)
        return "nie udało się zaktualizować notatki"