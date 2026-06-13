"""Unit tests for app.core.rag_pipeline.RAGPipeline, with all external APIs mocked."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.rag_pipeline import RAGPipeline


@pytest.fixture
def mock_embedder() -> MagicMock:
    embedder = MagicMock()
    embedder.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    return embedder


@pytest.fixture
def mock_vector_store() -> MagicMock:
    store = MagicMock()
    store.search.return_value = [
        {
            "text": "Paris is the capital of France.",
            "metadata": {
                "filename": "geography.txt",
                "page_number": 1,
                "chunk_index": 0,
                "doc_id": "doc-1",
            },
            "score": 0.92,
        }
    ]
    return store


@pytest.fixture
def mock_llm_client() -> MagicMock:
    client = MagicMock()
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="Paris is the capital of France [geography.txt, page 1].")],
        usage=SimpleNamespace(input_tokens=120, output_tokens=18),
    )
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def pipeline(mock_embedder: MagicMock, mock_vector_store: MagicMock, mock_llm_client: MagicMock) -> RAGPipeline:
    return RAGPipeline(
        embedder=mock_embedder,
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
    )


@pytest.mark.asyncio
async def test_ingest_chunks_embeds_and_stores_document(
    tmp_path: Path,
    pipeline: RAGPipeline,
    mock_embedder: MagicMock,
    mock_vector_store: MagicMock,
) -> None:
    file_path = tmp_path / "geography.txt"
    file_path.write_text("Paris is the capital of France. It is known for the Eiffel Tower.")

    result = await pipeline.ingest(str(file_path), "geography.txt", "doc-1")

    assert result == {"doc_id": "doc-1", "chunk_count": 1}
    mock_embedder.embed.assert_awaited_once()

    mock_vector_store.add_documents.assert_called_once()
    chunks_arg, doc_id_arg = mock_vector_store.add_documents.call_args[0]
    assert doc_id_arg == "doc-1"
    assert len(chunks_arg) == 1
    assert chunks_arg[0]["embedding"] == [0.1, 0.2, 0.3]
    assert chunks_arg[0]["metadata"]["filename"] == "geography.txt"
    assert chunks_arg[0]["metadata"]["chunk_index"] == 0


@pytest.mark.asyncio
async def test_ingest_unsupported_extension_raises_value_error(tmp_path: Path, pipeline: RAGPipeline) -> None:
    file_path = tmp_path / "image.png"
    file_path.write_bytes(b"not a real image")

    with pytest.raises(ValueError):
        await pipeline.ingest(str(file_path), "image.png", "doc-2")


@pytest.mark.asyncio
async def test_query_returns_answer_with_sources_and_token_usage(
    pipeline: RAGPipeline,
    mock_llm_client: MagicMock,
) -> None:
    result = await pipeline.query("What is the capital of France?", [])

    assert result["answer"] == "Paris is the capital of France [geography.txt, page 1]."
    assert result["tokens_used"] == 138  # 120 input + 18 output

    assert len(result["sources"]) == 1
    source = result["sources"][0]
    assert source["filename"] == "geography.txt"
    assert source["page"] == 1
    assert source["score"] == pytest.approx(0.92)

    mock_llm_client.messages.create.assert_awaited_once()
    _, kwargs = mock_llm_client.messages.create.call_args
    assert "Paris is the capital of France." in kwargs["messages"][0]["content"]
    assert "[Source: geography.txt, page 1]" in kwargs["messages"][0]["content"]


@pytest.mark.asyncio
async def test_query_with_no_relevant_chunks_uses_fallback_context(
    pipeline: RAGPipeline,
    mock_vector_store: MagicMock,
    mock_llm_client: MagicMock,
) -> None:
    mock_vector_store.search.return_value = []

    result = await pipeline.query("Unrelated question?", [])

    assert result["sources"] == []

    _, kwargs = mock_llm_client.messages.create.call_args
    assert "No relevant context" in kwargs["messages"][0]["content"]
