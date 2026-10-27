
from datetime import date
import re

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.embeddings import create_embedding
from app.services.generation import generate_answer
from app.services.chat_memory import (
    get_redis_client,
    get_history,
    add_messages,
)
from app.services.booking_flow import (
    get_booking_state,
    save_booking_state,
    clear_booking_state,
    create_interview_booking,
)
from app.services.booking_extraction import (
    extract_booking_details,
    next_booking_question,
)
from app.vectorstore.qdrant_store import search_chunks

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


def looks_like_booking_request(message: str) -> bool:
    """Identify an explicit request to schedule an interview."""
    text = message.lower()
    booking_terms = (
        "book an interview",
        "schedule an interview",
        "book interview",
        "schedule interview",
        "interview appointment",
        "arrange an interview",
    )
    return any(term in text for term in booking_terms)


def is_valid_booking_email(email: str) -> bool:
    """Perform a basic email-format check before saving."""
    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email,
        )
    )


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle conversational RAG and multi-turn interview booking."""

    session_id = request.session_id.strip()
    question = request.message.strip()

    if not session_id or not question:
        raise HTTPException(
            status_code=422,
            detail="Session ID and message must not be empty.",
        )

    redis = get_redis_client()

    try:
        history = await get_history(redis, session_id)
        booking_state = await get_booking_state(redis, session_id)

        # Start booking when the user explicitly requests an interview.
        if looks_like_booking_request(question) and not booking_state:
            booking_state = {"active": True}

        if booking_state.get("active"):
            booking_state = extract_booking_details(
                question,
                booking_state,
            )
            booking_state["active"] = True

            missing_question = next_booking_question(booking_state)

            if missing_question:
                answer = missing_question
                await save_booking_state(
                    redis,
                    session_id,
                    booking_state,
                )
            else:
                email = booking_state.get("email", "")
                if not is_valid_booking_email(email):
                    answer = (
                        "That email address doesn't appear valid. "
                        "Please provide a valid email address."
                    )
                    await save_booking_state(
                        redis,
                        session_id,
                        booking_state,
                    )
                else:
                    try:
                        booking = create_interview_booking(booking_state)
                    except ValueError as exc:
                        answer = (
                            f"{exc} Please provide a valid future date "
                            "and try again."
                        )
                        await save_booking_state(
                            redis,
                            session_id,
                            booking_state,
                        )
                    else:
                        await clear_booking_state(redis, session_id)
                        answer = (
                            "Your interview booking has been saved successfully. "
                            f"Booking reference: {booking['id']}. "
                            f"Name: {booking['candidate_name']}; "
                            f"email: {booking['email']}; "
                            f"date: {booking['interview_date']}; "
                            f"time: {booking['interview_time']}."
                        )

            await add_messages(
                redis,
                session_id,
                [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ],
            )
            return ChatResponse(
                session_id=session_id,
                answer=answer,
            )

        # Ordinary RAG conversation remains unchanged.
        history_text = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history[-10:]
        )

        query_embedding = await create_embedding(question)
        matches = await search_chunks(query_embedding, limit=5)

        context_parts = []
        for match in matches:
            payload = match.get("payload", {})
            chunk = payload.get("text")
            if chunk:
                context_parts.append(chunk)

        context = "\n\n---\n\n".join(context_parts)

        answer = await generate_answer(
            question=question,
            context=context,
            conversation_history=history_text,
        )

        await add_messages(
            redis,
            session_id,
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ],
        )

        return ChatResponse(
            session_id=session_id,
            answer=answer,
        )

    except Exception as exc:
        print("Chat error type:", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Chat processing failed. Check server logs.",
        ) from exc

    finally:
        await redis.aclose()
