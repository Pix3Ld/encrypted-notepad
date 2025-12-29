from datetime import datetime
from uuid import UUID

from domain.entities import Note, Trash
from domain.interfaces import NoteRepository, TrashRepository


class TrashNoteUseCase:
    def __init__(self, note_repo: NoteRepository, trash_repo: TrashRepository):
        self.note_repo = note_repo
        self.trash_repo = trash_repo

    async def execute(self, *, note_id: int, user_uuid: UUID) -> bool:
        note = await self.note_repo.get_by_id(
            note_id=note_id,
            user_uuid=user_uuid
        )

        if not note:
            return False

        trashed = Trash(
            id=note.id,
            title=note.title,
            content=note.content,
            user_uuid=user_uuid,
            tags=note.tags,
            created_at=note.created_at,
            trashed_at=datetime.utcnow(),
            key_private_b64=note.key_private_b64,
            public_key_b64=note.public_key_b64,
        )

        await self.trash_repo.add_to_trash(trashed)
        await self.note_repo.delete_notes(
            note_id=note_id,
            user_uuid=user_uuid
        )
        return True
