
from datetime import date, timedelta

from app.services.booking_extraction import (
    extract_booking_details,
    next_booking_question,
)


def test_extract_name_and_email():
    state = extract_booking_details(
        "My name is Alex Sharma and my email is alex@example.com.",
        {},
    )

    assert state["candidate_name"] == "Alex Sharma"
    assert state["email"] == "alex@example.com"


def test_extract_iso_date_and_time():
    future_date = (date.today() + timedelta(days=7)).isoformat()

    state = extract_booking_details(
        f"I prefer {future_date} at 10:30 AM.",
        {},
    )

    assert state["interview_date"] == future_date
    assert state["interview_time"] == "10:30:00"


def test_existing_details_are_preserved():
    existing = {
        "candidate_name": "Alex Sharma",
        "email": "alex@example.com",
    }

    state = extract_booking_details(
        "I prefer 10:30 AM.",
        existing,
    )

    assert state["candidate_name"] == "Alex Sharma"
    assert state["email"] == "alex@example.com"
    assert state["interview_time"] == "10:30:00"


def test_next_question_requests_missing_name():
    assert next_booking_question({}) is not None


def test_complete_details_need_no_follow_up():
    state = {
        "candidate_name": "Alex Sharma",
        "email": "alex@example.com",
        "interview_date": (date.today() + timedelta(days=7)).isoformat(),
        "interview_time": "10:30:00",
    }

    assert next_booking_question(state) is None
