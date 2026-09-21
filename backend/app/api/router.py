from fastapi import APIRouter

from app.api import analytics, auth, chat, conversations, health, users, voice

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(voice.router)
api_router.include_router(conversations.router)
api_router.include_router(analytics.router)
