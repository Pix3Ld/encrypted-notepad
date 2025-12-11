from typing import List

from domain.entities import Trash
from domain.interfaces import TrashRepository

from application.services.filtering.filter_dto import NotesFilter
from application.services.filtering.filtering_service import FilteringService

class FilterTrashUseCase:
    def __init__(self, repo: TrashRepository, filtering_service: FilteringService):
        self.repo = repo
        self.filtering = filtering_service

    async def execute(self, filters: NotesFilter) -> List[Trash]:
        return await self.filtering.filter_trash(self.repo, filters)