
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))
    chunking_strategy: Mapped[str] = mapped_column(String(50))
    chunk_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class InterviewBooking(Base):
    __tablename__ = "interview_bookings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    candidate_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), index=True)
    interview_date: Mapped[date] = mapped_column(Date)
    interview_time: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
