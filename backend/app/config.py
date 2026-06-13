"""Application configuration loaded from environment variables and .env files."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are loaded from environment variables first, falling back to a
    local ``.env`` file. See ``backend/.env.example`` for the full list of
    supported variables and their descriptions.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- External API credentials -------------------------------------------------
    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="API key for the Anthropic Claude API used to generate answers.",
    )
    OPENAI_API_KEY: str = Field(
        default="",
        description="API key for the OpenAI API used to generate text embeddings.",
    )

    # --- Vector store ---------------------------------------------------------------
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_data",
        description="Filesystem directory where ChromaDB persists its data.",
    )

    # --- Model configuration ----------------------------------------------------------
    LLM_MODEL: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Anthropic Claude model used to generate grounded answers.",
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model used to vectorize document chunks and queries.",
    )

    # --- Chunking ----------------------------------------------------------------------
    CHUNK_SIZE: int = Field(
        default=800,
        description="Target maximum number of characters per document chunk.",
    )
    CHUNK_OVERLAP: int = Field(
        default=150,
        description="Number of overlapping characters between consecutive chunks.",
    )

    # --- Retrieval -----------------------------------------------------------------------
    TOP_K_RESULTS: int = Field(
        default=5,
        description="Number of chunks retrieved from the vector store per query.",
    )

    # --- Uploads -------------------------------------------------------------------------
    MAX_FILE_SIZE_MB: int = Field(
        default=20,
        description="Maximum allowed upload size, in megabytes, for a single document.",
    )

    # --- CORS ------------------------------------------------------------------------------
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        description="List of allowed origins for CORS requests from the frontend.",
    )

    # --- App metadata ------------------------------------------------------------------------
    APP_VERSION: str = Field(
        default="0.1.0",
        description="Application version reported by the health endpoint.",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of :class:`Settings`."""
    return Settings()
