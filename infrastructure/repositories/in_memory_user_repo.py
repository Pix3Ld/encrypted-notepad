from typing import List, Optional
from domain.entities import User


class InMemoryUserRepository:
    def __init__(self):
        self._users: List[User] = []
        self._next_id = 1

    async def add_user(self, email: str, password_hash: str, created_at: Optional[str] = None) -> User:
        user = User(id=self._next_id, email=email, password_hash=password_hash, created_at=created_at)
        self._users.append(user)
        self._next_id += 1
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return next((u for u in self._users if u.id == user_id), None)

    async def get_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._users if u.email == email), None)
