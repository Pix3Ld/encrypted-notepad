from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService

class GetNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        self.repo = repo
        self.encryption = encryption
        '''ininciajlizacje . do self aby potem mozna bylo uzywac w metodach'''
        '''inaczej inicjalizer aka konstruktor'''
    def execute(self, note_id: int) -> str:
        '''odszyfrowanie notatki o podanym id'''
        note = self.repo.get_note_by_id(note_id)
        if not note:
            return "None"  # Używamy None zamiast stringa dla spójności
        return self.encryption.decryptserver(note.content)