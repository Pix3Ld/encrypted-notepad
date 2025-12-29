"""Moduł dostępu do bazy danych - Postgres z relacją 1:N -> users.uuid."""

import asyncio

from databases import Database
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import UUID, VARCHAR
from sqlalchemy import Integer, DateTime

from sqlalchemy.exc import OperationalError, DatabaseError
from asyncpg.exceptions import CannotConnectNowError, ConnectionDoesNotExistError

from presentation.config import config

metadata = sqlalchemy.MetaData()

users_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", Integer, autoincrement=True, primary_key=True),
    sqlalchemy.Column("email", VARCHAR(255), unique=True, nullable=False),
    sqlalchemy.Column("password_hash", VARCHAR(255), nullable=False),
    sqlalchemy.Column("uuid", UUID(as_uuid=True), unique=True, nullable=False),
    sqlalchemy.Column("created_at", DateTime(timezone=True), nullable=True),
)

notes_table = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", Integer, autoincrement=True, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.LargeBinary, nullable=False),
    sqlalchemy.Column("content", sqlalchemy.LargeBinary, nullable=False),
    sqlalchemy.Column("user_uuid", UUID(as_uuid=True), sqlalchemy.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("created_at", DateTime(timezone=True), nullable=True),
    sqlalchemy.Column("tags", sqlalchemy.ARRAY(VARCHAR), nullable=True),
    sqlalchemy.Column("key_private_b64", VARCHAR(255), nullable=True),
    sqlalchemy.Column("public_key_b64", VARCHAR(255), nullable=True),
)

trash_table = sqlalchemy.Table(
    "trash",
    metadata,
    sqlalchemy.Column("id", Integer, autoincrement=True, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.LargeBinary, nullable=False),
    sqlalchemy.Column("content", sqlalchemy.LargeBinary, nullable=False),
    sqlalchemy.Column("user_uuid", UUID(as_uuid=True), sqlalchemy.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False),
    sqlalchemy.Column("tags", sqlalchemy.ARRAY(VARCHAR), nullable=True),
    sqlalchemy.Column("created_at", DateTime(timezone=True), nullable=True),
    sqlalchemy.Column("trashed_at", DateTime(timezone=True), nullable=True),
    sqlalchemy.Column("key_private_b64", VARCHAR(255), nullable=True),
    sqlalchemy.Column("public_key_b64", VARCHAR(255), nullable=True),
)

DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}"#dla databases
SYNC_DATABASE_URL = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}"#dla engine

database = Database(DATABASE_URL)
engine = create_engine(SYNC_DATABASE_URL)


async def create_tables(database):
    """Funkcja tworząca tabele w bazie danych."""
    print("Starting create_tables")
    from sqlalchemy.schema import CreateTable

    for table in metadata.sorted_tables:
        ddl = str(CreateTable(table, if_not_exists=True).compile(engine))
        print(f"Executing DDL: {ddl}")
        await database.execute(ddl)
    print("Tabele zostały utworzone w bazie danych.")