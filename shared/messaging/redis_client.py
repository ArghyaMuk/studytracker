import logging

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Wrapper around Redis async client."""

    def __init__(self, redis_url: str):
        self._url = redis_url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        self._client = redis.from_url(self._url, decode_responses=True)

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def incr(self, key: str) -> int | None:
        try:
            return await self.client.incr(key)
        except redis.RedisError as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    async def expire(self, key: str, seconds: int) -> None:
        try:
            await self.client.expire(key, seconds)
        except redis.RedisError as e:
            logger.error(f"Redis EXPIRE error: {e}")

    async def close(self) -> None:
        if self._client:
            await self._client.close()


async def get_redis_client(redis_url: str) -> RedisClient:
    client = RedisClient(redis_url)
    await client.connect()
    return client
