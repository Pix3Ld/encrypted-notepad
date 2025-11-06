from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService

class GetNoteUseCase:
    def __init__(self,repo:NoteRepository,encryption:EncryptionService) -> None:
        '''ininciajlizacje . do self aby potem mozna bylo uzywac w metodach'''
        '''inaczej inicjalizer aka konstruktor'''
        self.repo=repo
        self.encrtyption=encryption
    def decrypt_note(self,note_id:int)->str:
        '''odszyfrowanie notatki o podanym id'''
        note=self.repo.get_note_by_id(note_id=note_id)
        if note is None:
            raise ValueError("nima kurwa")
        decrypted=self.encrtyption.decryptserver(note.content)
        return decrypted