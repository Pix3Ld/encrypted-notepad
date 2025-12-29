from typing import List, Optional,cast
from uuid import UUID
from datetime import datetime
from domain.entities import Note
from domain.interfaces import NoteRepository
from presentation.db import database, notes_table


class SQLNoteRepository(NoteRepository):
    async def add(self, note: Note) -> Note:
        query = (
            notes_table.insert()
            .values(
                user_uuid=note.user_uuid,
                title=note.title,
                content=note.content,
                tags=note.tags,
                created_at=note.created_at,
                key_private_b64=note.key_private_b64,
                public_key_b64=note.public_key_b64,
            )
            .returning(notes_table.c.id)
        )
        row = await database.fetch_one(query)
        if row:
            note.id = row["id"]
        return note

    async def get_by_id(self, *, note_id: int, user_uuid: UUID) -> Optional[Note]:
        query = notes_table.select().where(notes_table.c.id == note_id).where(notes_table.c.user_uuid == str(user_uuid))
        row = await database.fetch_one(query)
        if not row:
            return None
        return Note(id=row["id"], user_uuid=row["user_uuid"], title=row["title"], 
                    content=row["content"], created_at=row["created_at"], tags=row["tags"], 
                    key_private_b64=row["key_private_b64"],public_key_b64=row["public_key_b64"])

    async def get_all(self, *,user_uuid:UUID) -> List[Note]:
        rows = await database.fetch_all(
        notes_table.select().where(
            notes_table.c.user_uuid == str(user_uuid)
        )
    )
        return [
            Note(id=r["id"], user_uuid=r["user_uuid"], title=r["title"], content=r["content"], 
                 created_at=r["created_at"], tags=r["tags"], key_private_b64=r["key_private_b64"],
                 public_key_b64=r["public_key_b64"]) for r in rows
        ]

    async def update(
        self,
        note_id: int,
        *,
        user_uuid: UUID,
        title: Optional[bytes] = None,
        content: Optional[bytes] = None,
        tags: Optional[List[str]] = None,
        updated_at: Optional[datetime] = None,
    ) -> Optional[Note]:
        values = {}
        if content is not None:
            values["content"] = content
        if title is not None:
            values["title"] = title
        if tags is not None:
            values["tags"] = tags
        if updated_at is not None:
            values["updated_at"] = updated_at
        query = notes_table.update().where(notes_table.c.id == note_id).where(notes_table.c.user_uuid == str(user_uuid)).values(**values).returning(*notes_table.c)
        row = await database.fetch_one(query)
        if not row:
            return None
        return Note(id=row["id"], user_uuid=row["user_uuid"], title=row["title"], content=row["content"], created_at=row["created_at"], tags=row["tags"], key_private_b64=row["key_private_b64"], public_key_b64=row["public_key_b64"])

    async def delete_notes(self, note_id: int, *, user_uuid:UUID) -> bool:
        # attempt delete and return whether it existed
        row = await database.fetch_one(notes_table.select().where(notes_table.c.id == note_id).where(notes_table.c.user_uuid == str(user_uuid)))
        if not row:
            return False
        await database.execute(notes_table.delete().where(notes_table.c.id == note_id).where(notes_table.c.user_uuid == str(user_uuid)))
        return True
