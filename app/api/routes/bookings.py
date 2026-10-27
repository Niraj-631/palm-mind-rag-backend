
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import InterviewBooking
from app.db.session import get_db
from app.schemas.chat import InterviewBookingRequest

router = APIRouter(
    prefix="/api/v1/bookings",
    tags=["Interview Bookings"],
)


class InterviewBookingResponse(BaseModel):
    id: int
    candidate_name: str
    email: EmailStr
    interview_date: date
    interview_time: time
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post(
    "",
    response_model=InterviewBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    request: InterviewBookingRequest,
    db: Session = Depends(get_db),
) -> InterviewBookingResponse:
    """Validate and save an interview booking."""

    if request.interview_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Interview date cannot be in the past.",
        )

    booking = InterviewBooking(
        candidate_name=request.candidate_name.strip(),
        email=str(request.email),
        interview_date=request.interview_date,
        interview_time=request.interview_time,
    )

    try:
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return InterviewBookingResponse.model_validate(booking)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the interview booking.",
        ) from exc


@router.get(
    "/{booking_id}",
    response_model=InterviewBookingResponse,
)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
) -> InterviewBookingResponse:
    """Retrieve a saved booking by its ID."""

    booking = db.get(InterviewBooking, booking_id)

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview booking not found.",
        )

    return InterviewBookingResponse.model_validate(booking)
