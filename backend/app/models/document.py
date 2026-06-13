"""Pydantic models for document upload, listing, and deletion endpoints."""

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to a single chunk of a processed document."""

    filename: str = Field(..., description="Original filename the chunk was extracted from.")
    page_number: int = Field(..., description="1-indexed page (or section) number the chunk belongs to.")
    chunk_index: int = Field(..., description="0-indexed position of the chunk within the document.")


class DocumentUploadResponse(BaseModel):
    """Response returned after a document has been successfully ingested."""

    doc_id: str = Field(..., description="Unique identifier assigned to the uploaded document.")
    filename: str = Field(..., description="Original filename of the uploaded document.")
    chunk_count: int = Field(..., description="Number of chunks the document was split into.")
    status: str = Field(..., description="Status of the ingestion, e.g. 'success'.")


class DocumentInfo(BaseModel):
    """Summary information about a single document stored in the vector store."""

    doc_id: str = Field(..., description="Unique identifier of the document.")
    filename: str = Field(..., description="Original filename of the document.")
    chunk_count: int = Field(..., description="Number of chunks stored for this document.")


class DocumentListResponse(BaseModel):
    """Response payload for the document listing endpoint."""

    documents: list[DocumentInfo] = Field(..., description="All documents currently stored in the vector store.")


class DocumentDeleteResponse(BaseModel):
    """Response returned after a document has been deleted."""

    doc_id: str = Field(..., description="Identifier of the document that was deleted.")
    status: str = Field(..., description="Status of the deletion, e.g. 'deleted'.")
