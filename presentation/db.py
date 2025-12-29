"""Moduł dostępu do bazy danych - Postgres z relacją 1:N -> users.uuid."""

import asyncio

from databases import Database
import sqlalchemy
from sqlalchemy import create_engine, text
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
SYNC_DATABASE_URL = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}"#dla engine

database = Database(DATABASE_URL)
engine = create_engine(SYNC_DATABASE_URL)


async def create_tables(database):
    """Funkcja tworząca tabele w bazie danych."""
    print("Starting create_tables")
    print(f"Connecting to database at {config.DB_HOST}/{config.DB_NAME}")
    
    # Use the sync engine to create tables - this is the standard SQLAlchemy way
    # Run it in a thread executor since we're in an async context
    def _create_tables_sync():
        try:
            # Create all tables - metadata.create_all handles connections internally
            metadata.create_all(engine, checkfirst=True)
            print("Tabele zostały utworzone w bazie danych.")
            
            # Verify tables were created by querying information_schema
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """))
                tables = [row[0] for row in result]
                print(f"Tables in database: {', '.join(tables) if tables else 'None found'}")
        except Exception as e:
            print(f"Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # Retry logic in case database isn't ready yet
    max_retries = 5
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            await asyncio.to_thread(_create_tables_sync)
            print("Tables created successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"Failed to create tables after {max_retries} attempts: {e}")
                import traceback
                traceback.print_exc()
                raise