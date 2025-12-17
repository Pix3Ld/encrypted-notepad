from typing import List

from domain.entities import Trash
from domain.interfaces import TrashRepository, FilteringServiceInterface

from application.services.filtering.filter_dto import NotesFilter

class FilterTrashUseCase:
    def __init__(self, repo: TrashRepository, filtering_service: FilteringServiceInterface):
        """Initialize the use case with repository and filtering service.
        
        Args:
            repo: Repository for accessing trashed notes
            filtering_service: Service for performing filtering operations
        """
        self.repo = repo
        self.filtering = filtering_service

    async def execute(self, filters: NotesFilter) -> List[Trash]:
        """Execute the filtering operation.
        
        Args:
            filters: DTO containing filter criteria
            
        Returns:
            List of trashed notes matching the filter criteria
        """
        return await self.filtering.filter_trash(self.repo, filters)