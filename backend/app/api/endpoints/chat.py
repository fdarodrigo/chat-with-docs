"""Chat endpoint: retrieval-augmented question answering."""

from anthropic import AnthropicError
from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError

from app.api.dependencies import get_pipeline
from app.core.rag_pipeline import RAGPipeline
from app.models.chat import ChatRequest, ChatResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> ChatResponse:
    """Answer a question using retrieval-augmented generation over uploaded documents.

    Args:
        request: The user's question and prior conversation history.
        pipeline: Shared RAG pipeline dependency.

    Returns:
        The generated answer along with the source chunks used to ground it
        and the number of LLM tokens consumed.
    """
    history = [turn.model_dump() for turn in request.conversation_history]

    try:
        result = await pipeline.query(request.question, history)
    except (OpenAIError, AnthropicError) as exc:
        logger.error("chat_provider_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service is currently unavailable. Please try again later.",
        ) from exc

    logger.info(
        "chat_request_completed",
        question_length=len(request.question),
        source_count=len(result["sources"]),
        tokens_used=result["tokens_used"],
    )

    return ChatResponse(**result)
