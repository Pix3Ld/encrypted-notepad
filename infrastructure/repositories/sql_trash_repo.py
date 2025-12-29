from typing import List, Optional
from uuid import UUID

from domain.entities import Trash, Note
from domain.interfaces import TrashRepository
from presentation.db import database, trash_table


class SQLTrashRepository(TrashRepository):
    async def add_to_trash(self, trashed_note: Trash) -> Trash:
        query = (
            trash_table.insert()
            .values(
                user_uuid=trashed_note.user_uuid,
                title=trashed_note.title,
                content=trashed_note.content,
                tags=trashed_note.tags,
                created_at=trashed_note.created_at,
                trashed_at=trashed_note.trashed_at,
                key_private_b64=trashed_note.key_private_b64,
                public_key_b64=trashed_note.public_key_b64,
            )
            .returning(trash_table.c.id)
        )
        row = await database.fetch_one(query)
        if row:
            trashed_note.id = row["id"]
        return trashed_note

    async def get_by_id(self, *, note_id: int, user_uuid: UUID) -> Optional[Trash]:
        query = trash_table.select().where(trash_table.c.id == note_id).where(trash_table.c.user_uuid == str(user_uuid))
        row = await database.fetch_one(query)
        if not row:
            return None
        return Trash(id=row["id"], user_uuid=row["user_uuid"], 
                    title=row["title"], content=row["content"], tags=row["tags"],
                    created_at=row["created_at"], trashed_at=row["trashed_at"],
                    key_private_b64=row["key_private_b64"], public_key_b64=row["public_key_b64"])

    async def get_all(self, user_uuid: UUID) -> List[Trash]:
        rows = await database.fetch_all(trash_table.select().where(trash_table.c.user_uuid == str(user_uuid)))
        return [
            Trash(id=r["id"], user_uuid=r["user_uuid"], 
                  title=r["title"], content=r["content"], tags=r["tags"], 
                  created_at=r["created_at"], trashed_at=r["trashed_at"], 
                  key_private_b64=r["key_private_b64"],public_key_b64=r["public_key_b64"]) for r in rows
        ]

    async def restore(self, *, note_id: int, user_uuid: UUID) -> Optional[Note]:
        trashed = await self.get_by_id(note_id=note_id, user_uuid=user_uuid)
        if not trashed:
            return None
        # remove from trash
        await database.execute(trash_table.delete().where(trash_table.c.id == note_id).where(trash_table.c.user_uuid == str(user_uuid)))
        # construct Note from trashed
        note = Note(id=trashed.id, user_uuid=trashed.user_uuid, 
                    title=trashed.title, content=trashed.content, 
                    created_at=trashed.created_at, tags=trashed.tags, 
                    key_private_b64=trashed.key_private_b64, public_key_b64=trashed.public_key_b64)
        return note

    async def delete_permanently(self, *, note_id: int, user_uuid: UUID) -> bool:
        row = await database.fetch_one(trash_table.select().where(trash_table.c.id == note_id).where(trash_table.c.user_uuid == str(user_uuid)))
        if not row:
            return False
        await database.execute(trash_table.delete().where(trash_table.c.id == note_id).where(trash_table.c.user_uuid == str(user_uuid)))
        return True
