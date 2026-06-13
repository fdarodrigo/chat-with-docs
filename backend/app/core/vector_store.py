"""ChromaDB-backed persistent vector store for document chunks."""

from typing import Any

import chromadb

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "documents"


class VectorStore:
    """Thin wrapper around a persistent ChromaDB collection of document chunks."""

    def __init__(self, persist_dir: str | None = None) -> None:
        """Initialize the vector store.

        Args:
            persist_dir: Directory where ChromaDB persists its data. Defaults
                to ``CHROMA_PERSIST_DIR`` from application settings.
        """
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=persist_dir or settings.CHROMA_PERSIST_DIR)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, chunks: list[dict[str, Any]], doc_id: str) -> None:
        """Store embedded chunks for a document.

        Args:
            chunks: List of dicts, each containing ``text`` (str),
                ``metadata`` (dict), and ``embedding`` (list[float]) keys.
            doc_id: Identifier shared by all chunks belonging to this document.
        """
        if not chunks:
            return

        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        documents = [chunk["text"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]
        metadatas: list[dict[str, Any]] = []
        for chunk in chunks:
            metadata = dict(chunk["metadata"])
            metadata["doc_id"] = doc_id
            metadatas.append(metadata)

        self._collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        logger.info("vector_store_add", doc_id=doc_id, chunk_count=len(chunks))

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        score_threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Search for chunks most similar to a query embedding.

        Args:
            query_embedding: Embedding vector of the query.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score (0-1, higher is more
                similar) a chunk must reach to be included.

        Returns:
            A list of dicts with ``text``, ``metadata``, and ``score`` keys,
            ordered from most to least similar.
        """
        count = self._collection.count()
        if count == 0:
            return []

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
        )

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        matches: list[dict[str, Any]] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            score = max(0.0, 1.0 - distance)
            if score < score_threshold:
                continue
            matches.append({"text": text, "metadata": dict(metadata), "score": score})

        return matches

    def delete_document(self, doc_id: str) -> None:
        """Remove all chunks belonging to ``doc_id`` from the vector store."""
        self._collection.delete(where={"doc_id": doc_id})
        logger.info("vector_store_delete", doc_id=doc_id)

    def list_documents(self) -> list[str]:
        """Return the unique document ids currently stored."""
        results = self._collection.get(include=["metadatas"])
        doc_ids: set[str] = set()
        for metadata in results.get("metadatas") or []:
            if metadata and "doc_id" in metadata:
                doc_ids.add(str(metadata["doc_id"]))
        return sorted(doc_ids)

    def get_document_info(self) -> list[dict[str, Any]]:
        """Return aggregated ``{doc_id, filename, chunk_count}`` info for every stored document."""
        results = self._collection.get(include=["metadatas"])
        info: dict[str, dict[str, Any]] = {}

        for metadata in results.get("metadatas") or []:
            if not metadata or "doc_id" not in metadata:
                continue
            doc_id = str(metadata["doc_id"])
            if doc_id not in info:
                info[doc_id] = {
                    "doc_id": doc_id,
                    "filename": metadata.get("filename", "unknown"),
                    "chunk_count": 0,
                }
            info[doc_id]["chunk_count"] += 1

        return list(info.values())
