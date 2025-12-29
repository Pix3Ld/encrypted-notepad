import uuid
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from domain.entities import User
from domain.interfaces import UserRepository
from presentation.db import database, users_table


class SQLUserRepository(UserRepository):
    async def add(self, username: str, password_hash: str, created_at: Optional[datetime] = None) -> User:
        user_uuid = uuid.uuid4()
        query = (
            users_table.insert()
            .values(email=username, password_hash=password_hash, created_at=created_at, uuid=user_uuid)
            .returning(users_table.c.id, users_table.c.uuid, users_table.c.email, users_table.c.password_hash, users_table.c.created_at)
        )
        row = await database.fetch_one(query)
        if not row:
            raise ValueError("Failed to create user")
        return User(id=row["id"], uuid=row["uuid"], email=row["email"], password_hash=row["password_hash"], created_at=row["created_at"])

    async def get_by_id(self, user_id: int) -> Optional[User]:
        query = users_table.select().where(users_table.c.id == user_id)
        row = await database.fetch_one(query)
        if not row:
            return None
        return User(id=row["id"], uuid=row["uuid"], email=row["email"], password_hash=row["password_hash"], created_at=row["created_at"])

    async def get_by_email(self, email: str) -> Optional[User]:
        query = users_table.select().where(users_table.c.email == email)
        row = await database.fetch_one(query)
        if not row:
            return None
        return User(id=row["id"], uuid=row["uuid"], email=row["email"], password_hash=row["password_hash"], created_at=row["created_at"])

    async def get_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        query = users_table.select().where(users_table.c.uuid == str(user_uuid))
        row = await database.fetch_one(query)
        if not row:
            return None
        return User(id=row["id"], uuid=row["uuid"], email=row["email"], password_hash=row["password_hash"], created_at=row["created_at"])

    async def get_all(self) -> List[User]:
        from typing import List
        query = users_table.select()
        rows = await database.fetch_all(query)
        return [
            User(id=row["id"], uuid=row["uuid"], email=row["email"], password_hash=row["password_hash"], created_at=row["created_at"])
            for row in rows
        ]
