from fastapi import FastAPI
from presentation.api import notes_router, search_router, users_router , trash_router, permament_time_router, export_router, fitering_router

app = FastAPI(title="Szyfrowany Notatnik — Onion Architecture")
app.include_router(users_router.router)
app.include_router(notes_router.router)
app.include_router(trash_router.router)
app.include_router(permament_time_router.router)
app.include_router(export_router.router)
app.include_router(search_router.router)
app.include_router(fitering_router.router)