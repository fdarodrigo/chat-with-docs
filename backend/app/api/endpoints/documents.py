"""Document upload, listing, and deletion endpoints."""

import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from anthropic import AnthropicError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from openai import OpenAIError

from app.api.dependencies import get_pipeline
from app.config import get_settings
from app.core.rag_pipeline import RAGPipeline
from app.models.document import (
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    # Some browsers send a generic type for non-standard extensions.
    "application/octet-stream",
}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> DocumentUploadResponse:
    """Upload a document, validate it, and ingest it into the RAG pipeline.

    Args:
        file: The uploaded PDF, DOCX, or TXT file.
        pipeline: Shared RAG pipeline dependency.

    Returns:
        A summary of the ingestion, including the assigned ``doc_id`` and
        resulting ``chunk_count``.

    Raises:
        HTTPException: 415 if the file type is unsupported, 413 if the file
            exceeds the configured size limit, or 400 if processing fails.
    """
    settings = get_settings()
    filename = file.filename or "untitled"
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{extension}'. Allowed types: {sorted(ALLOWED_EXTENSIONS)}.",
        )

    contents = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB.",
        )

    doc_id = str(uuid.uuid4())
    with NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(contents)
        tmp_path = tmp_file.name

    try:
        result = await pipeline.ingest(tmp_path, filename, doc_id)
    except ValueError as exc:
        logger.warning("document_ingest_failed", filename=filename, error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (OpenAIError, AnthropicError) as exc:
        logger.error("document_ingest_provider_error", filename=filename, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The embedding service is currently unavailable. Please try again later.",
        ) from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    logger.info(
        "document_uploaded",
        doc_id=doc_id,
        filename=filename,
        chunk_count=result["chunk_count"],
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=filename,
        chunk_count=result["chunk_count"],
        status="success",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(pipeline: RAGPipeline = Depends(get_pipeline)) -> DocumentListResponse:
    """List all documents currently stored in the vector store."""
    documents = pipeline.vector_store.get_document_info()
    return DocumentListResponse(documents=[DocumentInfo(**doc) for doc in documents])


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: str,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> DocumentDeleteResponse:
    """Delete all chunks belonging to a document from the vector store.

    Args:
        doc_id: Identifier of the document to delete.
        pipeline: Shared RAG pipeline dependency.

    Returns:
        Confirmation that the document was deleted.

    Raises:
        HTTPException: 404 if no document with the given id exists.
    """
    if doc_id not in pipeline.vector_store.list_documents():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_id}' not found.")

    pipeline.vector_store.delete_document(doc_id)
    logger.info("document_deleted", doc_id=doc_id)
    return DocumentDeleteResponse(doc_id=doc_id, status="deleted")
