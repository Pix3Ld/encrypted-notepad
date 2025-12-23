from fastapi import FastAPI
from presentation.api import notes_router, users_router

app = FastAPI(title="Szyfrowany Notatnik — Onion Architecture")
app.include_router(notes_router.router)
app.include_router(users_router.router)