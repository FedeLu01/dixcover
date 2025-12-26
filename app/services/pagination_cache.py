import time
from typing import Any, Dict, List, Optional


class PaginationCache:
    """Simple in-memory cache for pagination results.

    Stores lists of items keyed by a string (e.g., source:domain) with a TTL.
    This is intentionally simple and suitable for local development; a
    production deployment should use a distributed cache (Redis) if needed.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, items: List[Dict]) -> None:
        self._store[key] = {"items": items, "ts": time.time()}

    def get(self, key: str) -> Optional[List[Dict]]:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() - entry["ts"] > self.ttl:
            # expired
            del self._store[key]
            return None
        return entry["items"]

    def clear(self, key: str) -> None:
        self._store.pop(key, None)


# module-level cache instance used by the app
cache = PaginationCache()
