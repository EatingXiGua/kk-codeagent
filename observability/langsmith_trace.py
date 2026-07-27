from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

try:
    from langsmith import traceable as _langsmith_traceable
except ImportError:
    _langsmith_traceable = None


def traceable(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    if _langsmith_traceable is None:
        def decorator(func: F) -> F:
            return func

        return decorator

    return _langsmith_traceable(*args, **kwargs)
