from collections.abc import Callable
import os
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

try:
    from langsmith import traceable as _langsmith_traceable
    from langsmith.wrappers import wrap_openai as _wrap_openai
except ImportError:
    _langsmith_traceable = None
    _wrap_openai = None


def is_langsmith_enabled() -> bool:
    tracing = os.getenv("LANGSMITH_TRACING", "").lower()
    api_key = os.getenv("LANGSMITH_API_KEY", "")

    return tracing == "true" and bool(api_key)


def traceable(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    if _langsmith_traceable is None:
        def decorator(func: F) -> F:
            return func

        return decorator

    return _langsmith_traceable(*args, **kwargs)


def wrap_openai_client(client: Any) -> Any:
    if _wrap_openai is None or not is_langsmith_enabled():
        return client

    return _wrap_openai(
        client,
        chat_name="MoonshotChat",
        completions_name="MoonshotCompletion",
    )


def get_langsmith_status() -> dict[str, str]:
    api_key = os.getenv("LANGSMITH_API_KEY", "")

    return {
        "tracing": os.getenv("LANGSMITH_TRACING", "false"),
        "project": os.getenv("LANGSMITH_PROJECT", "default"),
        "api_key": "configured" if api_key else "missing",
        "sdk": "installed" if _langsmith_traceable is not None else "missing",
    }
