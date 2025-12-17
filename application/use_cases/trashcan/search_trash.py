from typing import List

from domain.entities import Trash
from domain.interfaces import TrashRepository, SearchServiceInterface

from application.services.search.search_dto import NotesSearchQuery


class SearchTrashUseCase:
    """Use case for searching trashed notes by query string.
    
    Performs loose matching on title, content, and tags.
    """

    def __init__(self, repo: TrashRepository, search_service: SearchServiceInterface):
        """Initialize the use case with repository and search service.
        
        Args:
            repo: Repository for accessing trashed notes
            search_service: Service for performing search operations
        """
        self.repo = repo
        self.search_service = search_service

    async def execute(self, search_query: NotesSearchQuery) -> List[Trash]:
        """Execute the search operation.
        
        Args:
            search_query: DTO containing the search query string
            
        Returns:
            List of trashed notes matching the search query
        """
        return await self.search_service.search_trash(self.repo, search_query)

