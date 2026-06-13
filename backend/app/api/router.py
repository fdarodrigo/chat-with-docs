"""Aggregates all versioned API endpoint routers."""

from fastapi import APIRouter

from app.api.endpoints import chat, documents, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
