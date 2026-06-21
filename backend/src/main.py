# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import districts, scores, chat, simulator

app = FastAPI(title="HanoiOS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(districts.router)
app.include_router(scores.router)
app.include_router(chat.router)
app.include_router(simulator.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
