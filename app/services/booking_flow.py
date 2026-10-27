
import json
from datetime import date, datetime, time

from redis.asyncio import Redis

from app.db.models import InterviewBooking
from app.db.session import SessionLocal


def booking_state_key(session_id: str) -> str:
    return f"palm_mind:booking:{session_id}"


async def get_booking_state(
    redis: Redis,
    session_id: str,
) -> dict:
    """Retrieve partially collected interview details from Redis."""
    raw = await redis.get(booking_state_key(session_id))
    if not raw:
        return {}

    try:
        state = json.loads(raw)
        return state if isinstance(state, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


async def save_booking_state(
    redis: Redis,
    session_id: str,
    state: dict,
) -> None:
    """Store partially collected interview details for 24 hours."""
    await redis.set(
        booking_state_key(session_id),
        json.dumps(state),
        ex=86400,
    )


async def clear_booking_state(
    redis: Redis,
    session_id: str,
) -> None:
    await redis.delete(booking_state_key(session_id))


def create_interview_booking(state: dict) -> dict:
    """Validate and save complete interview details in SQLite."""
    required = ("candidate_name", "email", "interview_date", "interview_time")
    if any(not state.get(field) for field in required):
        raise ValueError("All interview details are required.")

    interview_date = date.fromisoformat(state["interview_date"])
    interview_time = time.fromisoformat(state["interview_time"])

    if interview_date < date.today():
        raise ValueError("The interview date cannot be in the past.")

    db = SessionLocal()
    try:
        booking = InterviewBooking(
            candidate_name=state["candidate_name"].strip(),
            email=state["email"].strip(),
            interview_date=interview_date,
            interview_time=interview_time,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        return {
            "id": booking.id,
            "candidate_name": booking.candidate_name,
            "email": booking.email,
            "interview_date": booking.interview_date.isoformat(),
            "interview_time": booking.interview_time.isoformat(),
        }
    finally:
        db.close()
