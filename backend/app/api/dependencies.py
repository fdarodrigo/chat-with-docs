"""Shared FastAPI dependencies for endpoint handlers."""

from fastapi import Request

from app.core.rag_pipeline import RAGPipeline


def get_pipeline(request: Request) -> RAGPipeline:
    """Return the application's shared :class:`RAGPipeline` instance.

    The pipeline is constructed once during application startup (see
    ``app.main.lifespan``) and stored on ``app.state`` so that the vector
    store, embedder, and LLM client are reused across requests.
    """
    return request.app.state.rag_pipeline
