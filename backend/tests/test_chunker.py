"""Unit tests for app.core.chunker.TextChunker."""

from app.core.chunker import TextChunker

METADATA = {"filename": "doc.txt", "page_number": 1, "chunk_index": 0}


def test_chunk_short_text_returns_single_chunk() -> None:
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "This is a short piece of text."

    chunks = chunker.chunk(text, METADATA)

    assert len(chunks) == 1
    assert chunks[0]["text"] == text
    assert chunks[0]["metadata"]["chunk_index"] == 0
    assert chunks[0]["metadata"]["filename"] == "doc.txt"
    assert chunks[0]["metadata"]["page_number"] == 1


def test_chunk_respects_chunk_size_limit() -> None:
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = " ".join(f"word{i}" for i in range(100))

    chunks = chunker.chunk(text, METADATA)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["text"]) <= chunker.chunk_size


def test_chunk_overlap_increases_total_characters() -> None:
    text = " ".join(f"word{i}" for i in range(100))

    no_overlap = TextChunker(chunk_size=50, chunk_overlap=0).chunk(text, METADATA)
    with_overlap = TextChunker(chunk_size=50, chunk_overlap=10).chunk(text, METADATA)

    no_overlap_total = sum(len(c["text"]) for c in no_overlap)
    with_overlap_total = sum(len(c["text"]) for c in with_overlap)

    assert with_overlap_total > no_overlap_total


def test_chunk_empty_text_returns_no_chunks() -> None:
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    assert chunker.chunk("   \n\n  ", METADATA) == []


def test_chunk_indices_are_sequential_and_metadata_preserved() -> None:
    chunker = TextChunker(chunk_size=20, chunk_overlap=5)
    text = (
        "Paragraph one.\n\n"
        "Paragraph two is intentionally longer than the chunk size limit "
        "configured for this particular test case.\n\n"
        "Paragraph three."
    )
    metadata = {"filename": "report.txt", "page_number": 3, "chunk_index": 0}

    chunks = chunker.chunk(text, metadata)

    assert len(chunks) > 1
    for index, chunk in enumerate(chunks):
        assert chunk["metadata"]["chunk_index"] == index
        assert chunk["metadata"]["filename"] == "report.txt"
        assert chunk["metadata"]["page_number"] == 3
