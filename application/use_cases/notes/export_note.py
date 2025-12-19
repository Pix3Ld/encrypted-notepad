from domain.interfaces import NoteRepository, ExportServiceInterface
from application.services.exporting.export_dto import NotesExport


class ExportNoteUseCase:
    """Use case for exporting a note to a text file.
    
    Exports a note by decrypting its title and content,
    then creating a .txt file with the title as filename
    and content as file content.
    """

    def __init__(self, repo: NoteRepository, export_service: ExportServiceInterface):
        """Initialize the use case.
        
        Args:
            repo: Repository for accessing notes
            export_service: Service for performing export operations
        """
        self.repo = repo
        self.export_service = export_service

    async def execute(self, export_request: NotesExport) -> tuple[str, str]:
        """Execute the export operation.
        
        Args:
            export_request: DTO containing the note ID to export
            
        Returns:
            Tuple containing (file_path, filename)
            
        Raises:
            ValueError: If note doesn't exist or decryption fails
        """
        return await self.export_service.exporting(export_request.note_id, self.repo)

