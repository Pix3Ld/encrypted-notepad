from domain.entities import Note
from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService

class CreateNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        '''konstruktor do inicjalizacji repozytorium i serwisu szyfrującego'''
        '''repozytorium aka baza danych'''
        self.repo = repo
        self.encryption = encryption
    def execute(self, local_encrypted_content: str) -> Note:
        '''wykorzystuje encryption service do ponownego zaszyfrowania notatki.
        wysłanej z klienta i zapisuje ją w repozytorium'''
        encrypted_for_server = self.encryption.encryptserver(local_encrypted_content)
        note = Note(id=len(self.repo.get_all()) + 1, content=encrypted_for_server)
        self.repo.add_note(note)
        return note
        