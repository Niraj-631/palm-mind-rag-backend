
from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.documents import router as documents_router
from app.api.routes.chat import router as chat_router
from app.api.routes.bookings import router as bookings_router

app = FastAPI(
    title=settings.app_name,
    description="Document ingestion, conversational RAG, and interview booking APIs.",
    version="1.0.0",
)

app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(bookings_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Palm Mind AI RAG Backend is running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": settings.app_name,
    }
