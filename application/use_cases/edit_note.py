from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService

class EditNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        self.repo = repo
        self.encryption = encryption

    async def execute(self, note_id: int, new_local_encrypted_content: str) -> str:
        '''Edytuje istniejącą notatkę o podanym ID, aktualizując jej zawartość'''
        existing_note = await self.repo.get_note_by_id(note_id)
        if not existing_note:
            return "nie ma notatki"
        
        encrypted_content = self.encryption.encryptserver(new_local_encrypted_content)
        updated_note = await self.repo.update_notes(note_id, encrypted_content)
        
        if updated_note:
            return self.encryption.decryptserver(updated_note.content)
        return "nie udało się zaktualizować notatki"