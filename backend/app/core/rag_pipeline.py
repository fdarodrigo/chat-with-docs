"""Orchestrates the end-to-end RAG pipeline: ingestion and grounded querying."""

from typing import Any

import anthropic

from app.config import get_settings
from app.core.chunker import TextChunker
from app.core.document_processor import DocumentProcessor
from app.core.embedder import Embedder
from app.core.vector_store import VectorStore
from app.utils.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based ONLY on the "
    "provided document context.\n\n"
    'If the answer is not found in the context, say "I couldn\'t find '
    'information about that in the provided documents."\n\n'
    "Always cite which document and section your answer comes from."
)

# Number of most recent user/assistant exchanges (a pair of messages each) to
# include when constructing the prompt.
MAX_HISTORY_EXCHANGES = 5
MAX_RESPONSE_TOKENS = 1024
SCORE_THRESHOLD = 0.3


class RAGPipeline:
    """Coordinates document ingestion and retrieval-augmented question answering."""

    def __init__(
        self,
        document_processor: DocumentProcessor | None = None,
        chunker: TextChunker | None = None,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
        llm_client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        """Initialize the pipeline, constructing default collaborators if not provided.

        Args:
            document_processor: Extracts text from uploaded files.
            chunker: Splits extracted text into overlapping chunks.
            embedder: Generates embeddings for chunks and queries.
            vector_store: Persists and searches chunk embeddings.
            llm_client: Anthropic client used to generate grounded answers.
        """
        settings = get_settings()
        self._settings = settings
        self._document_processor = document_processor or DocumentProcessor()
        self._chunker = chunker or TextChunker()
        self._embedder = embedder or Embedder()
        self._vector_store = vector_store or VectorStore()
        self._llm_client = llm_client or anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    @property
    def vector_store(self) -> VectorStore:
        """Underlying vector store, exposed for document listing/deletion endpoints."""
        return self._vector_store

    async def ingest(self, file_path: str, filename: str, doc_id: str) -> dict[str, Any]:
        """Process, chunk, embed, and store a document.

        Args:
            file_path: Path to the document on disk.
            filename: Original filename of the uploaded document.
            doc_id: Unique identifier to associate with this document's chunks.

        Returns:
            A dict with ``doc_id`` and ``chunk_count`` keys.
        """
        sections = self._document_processor.process(file_path, filename)

        all_chunks: list[dict[str, Any]] = []
        for section in sections:
            all_chunks.extend(self._chunker.chunk(section["text"], section["metadata"]))

        for index, chunk in enumerate(all_chunks):
            chunk["metadata"]["chunk_index"] = index

        if all_chunks:
            texts = [chunk["text"] for chunk in all_chunks]
            embeddings = await self._embedder.embed(texts)
            for chunk, embedding in zip(all_chunks, embeddings):
                chunk["embedding"] = embedding

        self._vector_store.add_documents(all_chunks, doc_id)

        logger.info(
            "rag_ingest_completed",
            doc_id=doc_id,
            filename=filename,
            chunk_count=len(all_chunks),
        )
        return {"doc_id": doc_id, "chunk_count": len(all_chunks)}

    async def query(self, question: str, conversation_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Answer a question using retrieval-augmented generation.

        Args:
            question: The user's natural language question.
            conversation_history: Prior conversation turns, oldest first, as
                dicts with ``role`` and ``content`` keys.

        Returns:
            A dict with ``answer`` (str), ``sources`` (list of dicts with
            ``text``, ``filename``, ``page``, ``score``), and ``tokens_used``
            (int) keys.
        """
        embeddings = await self._embedder.embed([question])
        query_embedding = embeddings[0]

        matches = self._vector_store.search(
            query_embedding,
            top_k=self._settings.TOP_K_RESULTS,
            score_threshold=SCORE_THRESHOLD,
        )

        prompt = self._build_prompt(question, matches, conversation_history)

        response = await self._llm_client.messages.create(
            model=self._settings.LLM_MODEL,
            max_tokens=MAX_RESPONSE_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        answer = "".join(block.text for block in response.content if block.type == "text")
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        sources = [
            {
                "text": match["text"],
                "filename": match["metadata"].get("filename", "unknown"),
                "page": match["metadata"].get("page_number", 0),
                "score": match["score"],
            }
            for match in matches
        ]

        logger.info(
            "rag_query_completed",
            retrieval_count=len(matches),
            retrieval_scores=[round(match["score"], 4) for match in matches],
            tokens_used=tokens_used,
        )

        return {"answer": answer, "sources": sources, "tokens_used": tokens_used}

    def _build_prompt(
        self,
        question: str,
        matches: list[dict[str, Any]],
        conversation_history: list[dict[str, Any]],
    ) -> str:
        """Assemble the user-turn prompt from retrieved context, history, and the question."""
        context = self._build_context(matches)
        history = self._build_history(conversation_history)
        return f"Context:\n{context}\n\nConversation history:\n{history}\n\nQuestion: {question}"

    @staticmethod
    def _build_context(matches: list[dict[str, Any]]) -> str:
        """Render retrieved chunks as a context block, each tagged with its source."""
        if not matches:
            return "(No relevant context was found in the uploaded documents.)"

        parts = []
        for match in matches:
            metadata = match["metadata"]
            source = f"{metadata.get('filename', 'unknown')}, page {metadata.get('page_number', '?')}"
            parts.append(f"[Source: {source}]\n{match['text']}")
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_history(conversation_history: list[dict[str, Any]]) -> str:
        """Render the last few conversation exchanges as plain text."""
        if not conversation_history:
            return "(none)"

        recent = conversation_history[-MAX_HISTORY_EXCHANGES * 2 :]
        lines = [f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in recent]
        return "\n".join(lines)
