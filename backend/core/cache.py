from __future__ import annotations

import hashlib
import json
import logging

import redis

from config import settings

logger = logging.getLogger(__name__)

_redis = redis.from_url(settings.redis_url, decode_responses=True)


def _cache_key(query_text: str, doc_ids: list[str],user_id: str) -> str:
    payload = json.dumps({"q": query_text, "docs": sorted(doc_ids),"u": user_id}, sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"qcache:{hashlib.sha256(payload.encode()).hexdigest()}"


def get_cached_query(query_text: str, doc_ids: list[str], user_id: str) -> dict | None:
    try:
        key = _cache_key(query_text, doc_ids, user_id)
        raw = _redis.get(key)
        if raw:
            logger.debug("Cache hit for query: %r", query_text[:60])
            return json.loads(raw)
    except Exception:
        logger.warning("Redis read failed — proceeding without cache")
    return None


def set_cached_query(query_text: str, doc_ids: list[str], user_id: str,result: dict) -> None:
    try:
        key = _cache_key(query_text, doc_ids,user_id)
        _redis.setex(key, settings.query_cache_ttl, json.dumps(result))
    except Exception:
        logger.warning("Redis write failed — result not cached")


def ping_redis() -> bool:
    try:
        return _redis.ping()
    except Exception:
        return False
    