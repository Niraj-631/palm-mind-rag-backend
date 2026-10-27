
import json

from redis.asyncio import Redis

from app.core.config import settings


def get_redis_client() -> Redis:
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL is missing from .env")

    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=10,
        socket_timeout=10,
    )


async def get_history(
    client: Redis,
    session_id: str,
) -> list[dict[str, str]]:
    key = f"palm_mind:chat:{session_id}"
    raw_messages = await client.lrange(key, 0, -1)

    history = []
    for raw in raw_messages:
        try:
            message = json.loads(raw)
            if (
                isinstance(message, dict)
                and message.get("role") in {"user", "assistant"}
                and isinstance(message.get("content"), str)
            ):
                history.append(message)
        except (json.JSONDecodeError, TypeError):
            continue

    return history


async def add_messages(
    client: Redis,
    session_id: str,
    messages: list[dict[str, str]],
    ttl_seconds: int = 86400,
) -> None:
    key = f"palm_mind:chat:{session_id}"

    if messages:
        serialized = [json.dumps(message) for message in messages]
        async with client.pipeline(transaction=True) as pipe:
            pipe.rpush(key, *serialized)
            pipe.ltrim(key, -20, -1)
            pipe.expire(key, ttl_seconds)
            await pipe.execute()
