import asyncio
import sys
from functools import wraps
from typing import Any, Callable, TypeVar, Awaitable, Union

from prompt_toolkit.application import in_terminal
from prompt_toolkit.application.application import _do_wait_for_enter
from prompt_toolkit.eventloop import run_in_executor_with_context

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


T = TypeVar("T")


def terminal(wait_for_enter: bool = False):
    def decorator(
        func: Callable[..., Union[T, Awaitable[T]]],
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async with in_terminal():
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await run_in_executor_with_context(
                        lambda: func(*args, **kwargs)
                    )

                if wait_for_enter:
                    await _do_wait_for_enter("Press ENTER to continue...")

            return result

        return wrapper

    return decorator


debug_stdout = create_redirector("debug_buffer", "stdout")
debug_stderr = create_redirector("debug_buffer", "stderr")
log_stdout = create_redirector("log_handler", "stdout")
log_stderr = create_redirector("log_handler", "stderr")
