import asyncio

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from presentation.db import  database, create_tables
from presentation.api import (
    notes_router, search_router, users_router,
    trash_router, permament_time_router, export_router, fitering_router
)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    await database.connect()
    await create_tables(database)
    
    yield

    await database.disconnect()
app = FastAPI(
    title="Szyfrowany Notatnik — Onion Architecture",
    lifespan=lifespan
    )

app.include_router(users_router.router)
app.include_router(notes_router.router)
app.include_router(trash_router.router)
app.include_router(permament_time_router.router)
app.include_router(export_router.router)
app.include_router(search_router.router)
app.include_router(fitering_router.router)