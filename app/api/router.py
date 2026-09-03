from fastapi import APIRouter

from app.api.endpoints import health, chat, research, documents, runs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(research.router)
api_router.include_router(documents.router)
api_router.include_router(runs.router)
