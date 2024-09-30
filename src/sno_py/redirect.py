import asyncio
import sys
from functools import wraps
from typing import Any, Callable, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])


def create_redirector(attr_name: str, stream_name: str):
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            from sno_py.snoedit import SnoEdit

            app = SnoEdit()
            original_stream = getattr(sys, stream_name)
            setattr(sys, stream_name, getattr(app, attr_name))
            try:
                result = await func(*args, **kwargs)
            finally:
                setattr(sys, stream_name, original_stream)
            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            from sno_py.snoedit import SnoEdit

            app = SnoEdit()
            original_stream = getattr(sys, stream_name)
            setattr(sys, stream_name, getattr(app, attr_name))
            try:
                result = func(*args, **kwargs)
            finally:
                setattr(sys, stream_name, original_stream)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper  # type: ignore

    return decorator


debug_stdout = create_redirector("debug_buffer", "stdout")
debug_stderr = create_redirector("debug_buffer", "stderr")
log_stdout = create_redirector("log_handler", "stdout")
log_stderr = create_redirector("log_handler", "stderr")
