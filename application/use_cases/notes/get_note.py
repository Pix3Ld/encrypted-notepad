from uuid import UUID
from domain.interfaces import NoteRepository
from application.services.encryption_service import EncryptionService
class GetNoteUseCase:
    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        '''ininciajlizacje . do self aby potem mozna bylo uzywac w metodach'''
        '''inaczej inicjalizer aka konstruktor'''
        self.repo = repo
        self.encryption = encryption
    async def execute(self, *,note_id: int,user_uuid:UUID) -> str:
        '''odszyfrowanie notatki o podanym id'''
        note = await self.repo.get_by_id(note_id=note_id,user_uuid=user_uuid)
        if not note:
            return "None"  # Używamy None zamiast stringa dla spójności
        return self.encryption.decryptserver(note.content)  # zwróci odszyfrowaną zawarotść 
    async def title_execute(self, *,note_id: int,user_uuid:UUID)-> str:
        '''odszyfrowanie notatki o podanym id'''
        note = await self.repo.get_by_id(note_id=note_id,user_uuid=user_uuid)
        if not note:
            return "None"  # Używamy None zamiast stringa dla spójności
        return self.encryption.decryptserver(note.title)  # zwróci odszyfrowaną zawarotść 
    