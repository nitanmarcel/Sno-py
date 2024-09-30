from typing import Any, Callable, Dict, TypeVar

T = TypeVar("T")


def singleton(cls: T) -> Callable[..., T]:
    instances: Dict[Any, Any] = {}

    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
