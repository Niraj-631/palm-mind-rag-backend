
import httpx

from app.core.config import settings


def _qdrant_url() -> str:
    if not settings.qdrant_url:
        raise RuntimeError("QDRANT_URL is missing from .env")
    return settings.qdrant_url.rstrip("/")


def _qdrant_headers() -> dict[str, str]:
    if not settings.qdrant_api_key:
        raise RuntimeError("QDRANT_API_KEY is missing from .env")
    return {"api-key": settings.qdrant_api_key}


async def create_collection(vector_size: int) -> dict:
    if vector_size <= 0:
        raise ValueError("vector_size must be positive")

    url = f"{_qdrant_url()}/collections/{settings.qdrant_collection}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=_qdrant_headers())

        if response.status_code == 200:
            return {"status": "already_exists"}

        if response.status_code != 404:
            response.raise_for_status()

        response = await client.put(
            url,
            headers=_qdrant_headers(),
            json={
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine",
                }
            },
        )
        response.raise_for_status()
        return response.json()


async def upsert_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    document_id: str,
    filename: str,
) -> dict:
    import uuid

    if len(chunks) != len(embeddings):
        raise ValueError("Each chunk must have one embedding")

    points = [
        {
            "id": str(uuid.uuid4()),
            "vector": vector,
            "payload": {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
                "text": chunk,
            },
        }
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings))
    ]

    if not points:
        return {"status": "no_points", "count": 0}

    url = (
        f"{_qdrant_url()}/collections/"
        f"{settings.qdrant_collection}/points?wait=true"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.put(
            url,
            headers={**_qdrant_headers(), "Content-Type": "application/json"},
            json={"points": points},
        )
        response.raise_for_status()
        return {"status": "stored", "count": len(points)}


async def search_chunks(
    query_embedding: list[float],
    limit: int = 5,
) -> list[dict]:
    url = (
        f"{_qdrant_url()}/collections/"
        f"{settings.qdrant_collection}/points/query"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers={**_qdrant_headers(), "Content-Type": "application/json"},
            json={
                "query": query_embedding,
                "limit": limit,
                "with_payload": True,
            },
        )
        response.raise_for_status()
        data = response.json()

    return data.get("result", {}).get("points", [])
