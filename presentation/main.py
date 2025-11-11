from fastapi import FastAPI
from presentation.api import notes_router

app = FastAPI(title="Szyfrowany Notatnik — Onion Architecture")
app.include_router(notes_router.router)