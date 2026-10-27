
import httpx

from app.core.config import settings

GEMINI_EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{settings.gemini_embedding_model}:embedContent"
)


async def create_embedding(text: str) -> list[float]:
    """Generate a vector embedding using the Gemini REST API."""
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    payload = {
        "model": f"models/{settings.gemini_embedding_model}",
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": "RETRIEVAL_DOCUMENT",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GEMINI_EMBEDDING_URL,
            params={"key": settings.gemini_api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data["embedding"]["values"]
