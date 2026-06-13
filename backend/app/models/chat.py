"""Pydantic models for the chat/query endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A single turn in the conversation history."""

    role: Literal["user", "assistant"] = Field(..., description="Who sent the message.")
    content: str = Field(..., description="Text content of the message.")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    question: str = Field(..., min_length=1, description="The user's natural language question.")
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list,
        description="Prior conversation turns, oldest first. Only the last 5 exchanges are used.",
    )


class SourceCitation(BaseModel):
    """A retrieved chunk that was used as supporting evidence for an answer."""

    text: str = Field(..., description="The text content of the retrieved chunk.")
    filename: str = Field(..., description="Filename of the source document.")
    page: int = Field(..., description="Page (or section) number the chunk was extracted from.")
    score: float = Field(..., description="Similarity score between the query and this chunk (0-1).")


class ChatResponse(BaseModel):
    """Response payload for the chat endpoint."""

    answer: str = Field(..., description="The generated answer, grounded in the retrieved context.")
    sources: list[SourceCitation] = Field(..., description="Chunks used as context for the answer.")
    tokens_used: int = Field(..., description="Total number of LLM tokens used to generate the answer.")
