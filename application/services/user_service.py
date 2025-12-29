from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from domain.interfaces import UserRepository

from passlib.hash import pbkdf2_sha256
from jose import jwt

from domain.entities import User


class UserService:
    def __init__(self, repository: UserRepository, jwt_secret: str, jwt_exp_seconds: int):
        self._repo: UserRepository = repository
        self._jwt_secret = jwt_secret
        self._jwt_exp_seconds = jwt_exp_seconds

    async def register_user(self, email: str, password: str) -> Optional[User]:
        existing = await self._repo.get_by_email(email)
        if existing:
            return None
        
        pw_hash = pbkdf2_sha256.hash(password)
        user = await self._repo.add(username=email, password_hash=pw_hash, created_at=datetime.utcnow())
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        user = await self._repo.get_by_email(email)
        if not user:
            return None
        try:
            valid = pbkdf2_sha256.verify(password, user.password_hash)
        except Exception:
            return None
        if not valid:
            return None

        expires = datetime.utcnow() + timedelta(seconds=self._jwt_exp_seconds)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": int(expires.timestamp()),
        }
        token = jwt.encode(payload, self._jwt_secret, algorithm="HS256")
        return {
            "token_type": "bearer",
            "user_token": token,
            "expires": expires,
        }

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            data = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
            return data
        except Exception:
            return None
