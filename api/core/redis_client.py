import json
from functools import lru_cache
from typing import Any

import redis

from api.core.config import get_settings


@lru_cache
def _client() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def cache_get_json(key: str) -> Any | None:
    try:
        raw = _client().get(key)
    except redis.RedisError:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set_json(key: str, value: Any, timeout: int) -> None:
    try:
        _client().setex(key, timeout, json.dumps(value, default=str))
    except redis.RedisError:
        pass
