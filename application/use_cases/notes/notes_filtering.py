from typing import List

from domain.entities import Note
from domain.interfaces import NoteRepository, FilteringServiceInterface

from application.services.filtering.filter_dto import NotesFilter

class FilterNotesUseCase:
    def __init__(self, repo: NoteRepository, filter_service: FilteringServiceInterface) -> None:
        """Initialize the use case with repository and filtering service.
        
        Args:
            repo: Repository for accessing notes
            filter_service: Service for performing filtering operations
        """
        self.repo = repo
        self.filtering = filter_service
    
    
    async def execute(self, filters: NotesFilter) -> List[Note]:
        """Execute the filtering operation.
        
        Args:
            filters: DTO containing filter criteria
            
        Returns:
            List of notes matching the filter criteria
        """
        return await self.filtering.filter_notes(self.repo, filters,user_uuid=filters.user_uuid)