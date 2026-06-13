"""Health check endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_pipeline
from app.config import get_settings
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()


class HealthResponse(BaseModel):
    """Response payload for the health check endpoint."""

    status: str = Field(..., description="Overall service status, e.g. 'ok'.")
    version: str = Field(..., description="Application version.")
    documents_count: int = Field(..., description="Number of documents currently stored.")


@router.get("", response_model=HealthResponse)
async def health_check(pipeline: RAGPipeline = Depends(get_pipeline)) -> HealthResponse:
    """Return basic service status, version, and document count."""
    settings = get_settings()
    documents_count = len(pipeline.vector_store.list_documents())
    return HealthResponse(status="ok", version=settings.APP_VERSION, documents_count=documents_count)
