import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "kimi-k2.6"


def create_langchain_moonshot(
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 120.0,
    temperature: float = 1.0,
) -> ChatOpenAI:
    load_dotenv()

    resolved_api_key = api_key or os.getenv("MOONSHOT_API_KEY")
    resolved_model = model or os.getenv("MOONSHOT_MODEL") or DEFAULT_MODEL
    resolved_base_url = (
        base_url
        or os.getenv("MOONSHOT_BASE_URL")
        or DEFAULT_BASE_URL
    )

    if not resolved_api_key:
        raise ValueError("MOONSHOT_API_KEY is required")

    if timeout <= 0:
        raise ValueError("timeout must be greater than 0")

    return ChatOpenAI(
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        model=resolved_model,
        timeout=timeout,
        temperature=temperature,
    )
