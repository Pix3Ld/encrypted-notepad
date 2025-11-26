from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService
from typing import Optional

class EditNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        self.repo = repo
        self.encryption = encryption

    async def execute(self, note_id: int, new_local_encrypted_content: str, new_client_private_key_b64: Optional[str] = None) -> str:
        '''Edytuje istniejącą notatkę o podanym ID, aktualizując jej zawartość i klucz prywatny.'''
        existing_note = await self.repo.get_note_by_id(note_id)
        if not existing_note:
            return "nie ma notatki"
        
        encrypted_content = self.encryption.encryptserver(new_local_encrypted_content)
        # Update the note with new encrypted content and potentially new private key
        existing_note.content = encrypted_content
        if new_client_private_key_b64:
            existing_note.key_private_b64 = new_client_private_key_b64
        
        updated_note = await self.repo.update_notes(note_id, encrypted_content)
        
        if updated_note:
            # Also update the key if provided
            if new_client_private_key_b64:
                updated_note.key_private_b64 = new_client_private_key_b64
            return self.encryption.decryptserver(updated_note.content)
        return "nie udało się zaktualizować notatki"