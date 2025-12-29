from domain.interfaces import TrashRepository, UserRepository
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional

class DeleteXTime:
    """
    Serwis do permanentnego usuwania notatek z kosza po określonym czasie.
    """

    def __init__(self, trashcan: TrashRepository, ttl_days: int = 30, user_repo: Optional[UserRepository] = None):
        self._trash = trashcan
        self._ttl = timedelta(days=ttl_days)
        self._user_repo = user_repo

    async def execute(self, note_id: int,user_uuid:UUID) -> bool:
        trashed = await self._trash.get_by_id(note_id=note_id,user_uuid=user_uuid)
        if trashed is None or trashed.trashed_at is None:
            return False

        if datetime.utcnow() >= trashed.trashed_at + self._ttl:
            return await self._trash.delete_permanently(note_id=note_id,user_uuid=user_uuid)

        return False

    async def execute_all(self,user_uuid:UUID) -> int:
        all_trashed = await self._trash.get_all(user_uuid=user_uuid)
        deleted_count = 0
        now = datetime.utcnow()

        for trashed in all_trashed:
            if trashed.trashed_at is None:
                continue

            if now >= trashed.trashed_at + self._ttl:
                if await self._trash.delete_permanently(note_id=trashed.id,user_uuid=user_uuid):
                    deleted_count += 1

        return deleted_count
