from collections import OrderedDict
from typing import Any

from cache.any_cache import AnyCache


class LRUCache(AnyCache):
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: str) -> Any:
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return None

    def set(self, key: str, val: Any):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = val

    def key_exists(self, key):
        return key in self.cache
