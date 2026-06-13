"""Extracts raw text and metadata from uploaded PDF, DOCX, and TXT files."""

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from docx import Document as DocxDocument

from app.utils.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class DocumentProcessor:
    """Extracts text sections and metadata from supported document types."""

    def process(self, file_path: str, filename: str) -> list[dict[str, Any]]:
        """Extract text sections from a document.

        Each returned section corresponds to a page (PDF), the full body
        (DOCX), or the full file content (TXT). Sections are later split into
        smaller chunks by :class:`app.core.chunker.TextChunker`.

        Args:
            file_path: Path to the file on disk.
            filename: Original filename, used for metadata and to detect the
                file type from its extension.

        Returns:
            A list of dicts, each with a ``text`` key (str) and a
            ``metadata`` dict containing ``filename``, ``page_number``, and
            ``chunk_index``.

        Raises:
            ValueError: If the file extension is not one of ``.pdf``,
                ``.docx``, or ``.txt``.
        """
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            sections = self._process_pdf(file_path, filename)
        elif extension == ".docx":
            sections = self._process_docx(file_path, filename)
        elif extension == ".txt":
            sections = self._process_txt(file_path, filename)
        else:
            raise ValueError(f"Unsupported file type: '{extension}'. Supported types: {sorted(SUPPORTED_EXTENSIONS)}")

        logger.info(
            "document_processed",
            filename=filename,
            extension=extension,
            section_count=len(sections),
        )
        return sections

    def _process_pdf(self, file_path: str, filename: str) -> list[dict[str, Any]]:
        """Extract text page-by-page from a PDF using PyMuPDF."""
        sections: list[dict[str, Any]] = []
        with fitz.open(file_path) as pdf:
            for page_index, page in enumerate(pdf):
                text = page.get_text().strip()
                if not text:
                    continue
                sections.append(
                    {
                        "text": text,
                        "metadata": {
                            "filename": filename,
                            "page_number": page_index + 1,
                            "chunk_index": 0,
                        },
                    }
                )
        return sections

    def _process_docx(self, file_path: str, filename: str) -> list[dict[str, Any]]:
        """Extract text from all paragraphs of a DOCX file."""
        document = DocxDocument(file_path)
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        if not text:
            return []
        return [
            {
                "text": text,
                "metadata": {
                    "filename": filename,
                    "page_number": 1,
                    "chunk_index": 0,
                },
            }
        ]

    def _process_txt(self, file_path: str, filename: str) -> list[dict[str, Any]]:
        """Read the full content of a plain text file."""
        with open(file_path, encoding="utf-8", errors="replace") as f:
            text = f.read().strip()
        if not text:
            return []
        return [
            {
                "text": text,
                "metadata": {
                    "filename": filename,
                    "page_number": 1,
                    "chunk_index": 0,
                },
            }
        ]
