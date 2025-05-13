from .any_cache import AnyCache
from .lru_cache import LRUCache

_cache_instance: AnyCache | None = None


def get_cache() -> AnyCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LRUCache(100)
    return _cache_instance
