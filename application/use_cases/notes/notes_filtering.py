from typing import List

from domain.entities import Note
from domain.interfaces import NoteRepository

from application.services.filtering.filter_dto import NotesFilter
from application.services.filtering.filtering_service import FilteringService

class FilterNotesUseCase:
    def __init__(self,repo:NoteRepository,filter:FilteringService) -> None:
        self.repo=repo
        self.filtering=filter
    async def execute(self,filters:NotesFilter):
        return await self.filtering.filter_notes(self.repo,filters)