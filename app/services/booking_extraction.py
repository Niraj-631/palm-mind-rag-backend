
import json
import re
from datetime import date, datetime, time
from email_validator import EmailNotValidError, validate_email

from app.services.generation import generate_answer


def extract_booking_details(message: str, existing: dict) -> dict:
    """Extract explicitly provided interview details from a message."""
    state = dict(existing)

    # Extract email only when the message contains a valid email address.
    email_match = re.search(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        message,
    )
    if email_match:
        try:
            state["email"] = validate_email(
                email_match.group(0),
                check_deliverability=False,
            ).normalized
        except EmailNotValidError:
            pass

    # Extract an ISO date such as 2026-11-15.
    date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message)
    if date_match:
        try:
            parsed_date = date.fromisoformat(date_match.group(0))
            if parsed_date >= date.today():
                state["interview_date"] = parsed_date.isoformat()
        except ValueError:
            pass

    # Extract a time such as 10:30 or 10:30 AM.
    time_match = re.search(
        r"\b(1[0-2]|0?[1-9]):([0-5]\d)\s*(AM|PM)\b"
        r"|\b([01]?\d|2[0-3]):([0-5]\d)\b",
        message,
        re.IGNORECASE,
    )
    if time_match:
        try:
            if time_match.group(3):
                hour = int(time_match.group(1)) % 12
                if time_match.group(3).upper() == "PM":
                    hour += 12
                minute = int(time_match.group(2))
                parsed_time = time(hour, minute)
            else:
                parsed_time = time(
                    int(time_match.group(4)),
                    int(time_match.group(5)),
                )
            state["interview_time"] = parsed_time.isoformat()
        except (ValueError, TypeError):
            pass

    # Extract a name only when the message clearly states it.
    name_match = re.search(
        r"\b(?:my name is|name is|i am|i'm)\s+"
        r"([A-Za-z][A-Za-z .'-]{1,98})",
        message,
        re.IGNORECASE,
    )
    if name_match:
        candidate_name = name_match.group(1).strip(" .,'")
        candidate_name = re.split(
            r"\s+(?:and my email|my email|email is|and i want)\b",
            candidate_name,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()
        if candidate_name:
            state["candidate_name"] = candidate_name[:200]

    return state


def next_booking_question(state: dict) -> str | None:
    """Ask for the first missing required field."""
    if not state.get("candidate_name"):
        return "I'd be happy to help book an interview. What is your full name?"

    if not state.get("email"):
        return "Thanks! What email address should we use for the interview?"

    if not state.get("interview_date"):
        return (
            "What interview date would you prefer? "
            "Please use YYYY-MM-DD, for example 2026-11-15."
        )

    if not state.get("interview_time"):
        return (
            "What interview time would you prefer? "
            "Please use a time such as 10:30 AM."
        )

    return None
