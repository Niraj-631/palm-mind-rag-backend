
from datetime import date, time
from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=5000)


class ChatResponse(BaseModel):
    session_id: str
    answer: str


class InterviewBookingRequest(BaseModel):
    candidate_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    interview_date: date
    interview_time: time
