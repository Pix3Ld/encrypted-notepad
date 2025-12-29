import base64
import tempfile
import os
from uuid import UUID
from typing import Optional, cast

from domain.interfaces import NoteRepository, ExportServiceInterface
from application.services.encryption_service import EncryptionService


class ExportingService(ExportServiceInterface):
    """Service dla exportingu notes do pliku txt.
    
    Przeprowadza odszyfrowywanie title i content,
    tworzy plik .txt o nazwie title z zawartością content.
    """

    def __init__(self, repo: NoteRepository, encryption: EncryptionService):
        """Initialize export service.
        
        Args:
            repo: Repository for accessing notes
            encryption: Service for decrypting note data
        """
        self.encryption = encryption
        self.repo = repo

    async def _decrypt_title(self, title_bytes: Optional[bytes], key_private_b64: Optional[str], note_id: int,user_uuid:UUID) -> Optional[str]:
        """Odszyfrowuje tytuł notatki.
        
        Args:
            title_bytes: Encrypted title bytes
            key_private_b64: Base64 encoded private key
            note_id: ID of the note
            
        Returns:
            Decrypted title string or None if decryption fails
        """
        if not title_bytes or not key_private_b64:
            return None
        
        try:
            note = await self.repo.get_by_id(note_id=note_id,user_uuid=user_uuid)
            if note and note.title == title_bytes and note.key_private_b64 == key_private_b64:
                priv = base64.b64decode(cast(bytes, note.key_private_b64))
                tit_dec = self.encryption.decrypt_server(title_bytes)
                priv_dec = self.encryption.decrypt_with_private(tit_dec.encode(), priv)
                return priv_dec
        except Exception:
            return None
        
        return None
    
    async def _decrypt_content(self, content_bytes: Optional[bytes], key_private_b64: Optional[str], note_id: int,user_uuid:UUID) -> Optional[str]:
        """Odszyfrowuje zawartość notatki.
        
        Args:
            content_bytes: Encrypted content bytes
            key_private_b64: Base64 encoded private key
            note_id: ID of the note
            
        Returns:
            Decrypted content string or None if decryption fails
        """
        if not content_bytes or not key_private_b64:
            return None
        
        try:
            note = await self.repo.get_by_id(note_id=note_id,user_uuid=user_uuid)
            if note and note.content == content_bytes and note.key_private_b64 == key_private_b64:
                priv = base64.b64decode(cast(bytes, key_private_b64))
                content_dec = self.encryption.decrypt_server(content_bytes)
                content_decrypt = self.encryption.decrypt_with_private(content_dec.encode(), priv)
                return content_decrypt
        except Exception:
            return None
        
        return None

    async def export(self, note_id: int, repo: NoteRepository, user_uuid: UUID) -> tuple[str, str]:
        """Exportuje notatkę do pliku tekstowego.
        
        Args:
            note_id: ID notatki do wyeksportowania
            repo: Repository dla dostępu do notatek
            
        Returns:
            Tuple zawierający (ścieżka do pliku, nazwa pliku)
            
        Raises:
            ValueError: Jeśli notatka nie istnieje lub odszyfrowanie się nie powiodło
        """
        note = await repo.get_by_id(note_id=note_id,user_uuid=user_uuid)
        if not note:
            raise ValueError(f"Notatka o ID {note_id} nie istnieje")

        # Odszyfruj tytuł i zawartość
        decrypted_title = await self._decrypt_title(note.title, note.key_private_b64, note_id,user_uuid)
        decrypted_content = await self._decrypt_content(note.content, note.key_private_b64, note_id,user_uuid)

        if not decrypted_title or not decrypted_content:
            raise ValueError("Nie udało się odszyfrować tytułu lub zawartości notatki")

        # Utwórz bezpieczną nazwę pliku z tytułu (usuń znaki niedozwolone)
        safe_filename = "".join(c for c in decrypted_title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_filename:
            safe_filename = f"note_{note_id}"
        filename = f"{safe_filename}.txt"

        # Utwórz tymczasowy plik
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)

        # Zapisz zawartość do pliku
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(decrypted_content)
        except Exception as e:
            raise ValueError(f"Nie udało się utworzyć pliku: {e}")

        return file_path, filename
    