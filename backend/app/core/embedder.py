"""Async wrapper around the OpenAI embeddings API with batching and retries."""

import asyncio

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 100
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

RETRYABLE_ERRORS = (APIError, APIConnectionError, RateLimitError)


class Embedder:
    """Generates text embeddings using the OpenAI embeddings API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Initialize the embedder.

        Args:
            api_key: OpenAI API key. Defaults to ``OPENAI_API_KEY`` from settings.
            model: Embedding model name. Defaults to ``EMBEDDING_MODEL`` from settings.
        """
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self._model = model or settings.EMBEDDING_MODEL

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts, batching requests and retrying on transient errors.

        Args:
            texts: Input strings to embed.

        Returns:
            A list of embedding vectors, one per input text, in the same order
            as ``texts``. Returns an empty list if ``texts`` is empty.
        """
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start : start + BATCH_SIZE]
            embeddings.extend(await self._embed_batch(batch))
        return embeddings

    async def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        """Embed a single batch of texts, retrying with exponential backoff."""
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.embeddings.create(model=self._model, input=batch)
                return [item.embedding for item in response.data]
            except RETRYABLE_ERRORS as exc:
                last_error = exc
                wait_seconds = INITIAL_BACKOFF_SECONDS * (2**attempt)
                logger.warning(
                    "embedding_request_failed",
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES,
                    wait_seconds=wait_seconds,
                    error=str(exc),
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(wait_seconds)

        assert last_error is not None
        raise last_error
