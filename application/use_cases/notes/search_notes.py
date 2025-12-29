from typing import List

from domain.entities import Note
from domain.interfaces import NoteRepository, SearchServiceInterface

from application.services.search.search_dto import NotesSearchQuery


class SearchNotesUseCase:
    """Use case for searching notes by query string.
    
    Performs loose matching on title, content, and tags.
    """

    def __init__(self, repo: NoteRepository, search_service: SearchServiceInterface):
        """Initialize the use case with repository and search service.
        
        Args:
            repo: Repository for accessing notes
            search_service: Service for performing search operations
        """
        self.repo = repo
        self.search_service = search_service


    async def execute(self, search_query: NotesSearchQuery) -> List[Note]:
        """Execute the search operation.
        
        Args:
            search_query: DTO containing the search query string
            
        Returns:
            List of notes matching the search query
        """
        return await self.search_service.search_notes(self.repo, search_query,user_uuid=search_query.user_uuid)

