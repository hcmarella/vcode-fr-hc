from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    about,
    auth,
    chat,
    commands,
    images,
    knowledge,
    personas,
    skills,
    sync,
    sync_status,
    webhooks,
)

app = FastAPI(title="vcode-fr-hc portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(personas.router)
app.include_router(skills.router)
app.include_router(commands.router)
app.include_router(knowledge.router)
app.include_router(about.router)
app.include_router(sync.router)
app.include_router(sync_status.router)
app.include_router(chat.router)
app.include_router(images.router)
app.include_router(webhooks.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
