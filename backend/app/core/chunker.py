"""Manual implementation of recursive character-based text splitting."""

from typing import Any

from app.config import get_settings

# Ordered from coarsest to finest granularity. The splitter tries each
# separator in turn, recursing into the next one only when a piece is still
# larger than the target chunk size. An empty string falls back to splitting
# on individual characters.
DEFAULT_SEPARATORS: list[str] = ["\n\n", "\n", ". ", " ", ""]


class TextChunker:
    """Splits text into overlapping chunks using a recursive character splitter."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        """Initialize the chunker.

        Args:
            chunk_size: Target maximum number of characters per chunk.
                Defaults to ``CHUNK_SIZE`` from application settings.
            chunk_overlap: Number of characters of overlap between
                consecutive chunks. Defaults to ``CHUNK_OVERLAP`` from
                application settings.
        """
        settings = get_settings()
        self.chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    def chunk(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Split text into chunks, preserving and extending the given metadata.

        Args:
            text: The text to split.
            metadata: Metadata to copy into every produced chunk. A
                ``chunk_index`` key is added (or overwritten) on each chunk,
                numbered sequentially starting from 0.

        Returns:
            A list of dicts, each with a ``text`` key and a ``metadata`` dict.
        """
        text = text.strip()
        if not text:
            return []

        pieces = self._split_text(text, DEFAULT_SEPARATORS)
        merged = self._merge_pieces(pieces)

        chunks: list[dict[str, Any]] = []
        for index, chunk_text in enumerate(merged):
            chunk_metadata = {**metadata, "chunk_index": index}
            chunks.append({"text": chunk_text, "metadata": chunk_metadata})
        return chunks

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split ``text`` into pieces no larger than ``chunk_size``."""
        separator = separators[0]
        next_separators = separators[1:]

        if separator == "":
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        raw_splits = text.split(separator)

        pieces: list[str] = []
        for i, split in enumerate(raw_splits):
            piece = split
            if i < len(raw_splits) - 1:
                piece += separator
            if not piece:
                continue

            if len(piece) <= self.chunk_size:
                pieces.append(piece)
            elif next_separators:
                pieces.extend(self._split_text(piece, next_separators))
            else:
                pieces.extend(self._split_text(piece, [""]))

        return pieces

    def _merge_pieces(self, pieces: list[str]) -> list[str]:
        """Greedily merge small pieces into chunks of up to ``chunk_size`` with overlap."""
        chunks: list[str] = []
        current = ""

        for piece in pieces:
            if not current:
                current = piece
                continue

            if len(current) + len(piece) <= self.chunk_size:
                current += piece
                continue

            chunks.append(current.strip())
            overlap = current[-self.chunk_overlap :] if self.chunk_overlap > 0 else ""
            current = overlap + piece

        if current.strip():
            chunks.append(current.strip())

        return [c for c in chunks if c]
