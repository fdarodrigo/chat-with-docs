"""FastAPI application factory: app instance, lifespan, middleware, and routing."""

import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.core.rag_pipeline import RAGPipeline
from app.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize shared application resources on startup and clean up on shutdown."""
    settings = get_settings()
    logger.info("app_startup", version=settings.APP_VERSION, llm_model=settings.LLM_MODEL)
    app.state.rag_pipeline = RAGPipeline()
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Chat With Your Docs",
        description="A retrieval-augmented generation API for asking questions about uploaded documents.",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Log each request with a unique request_id, method, endpoint, and duration."""
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "request_completed",
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
