from abc import ABC, abstractmethod
from typing import Any


class AnyCache(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, val: Any):
        pass

    @abstractmethod
    def key_exists(self, key: str) -> bool:
        pass
