from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import about, auth, commands, knowledge, personas, skills, sync

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


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
