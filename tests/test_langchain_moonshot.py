from langchain_openai import ChatOpenAI

from llm import create_langchain_moonshot


def test_create_langchain_moonshot_from_environment(
    monkeypatch,
):
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-api-key")
    monkeypatch.setenv("MOONSHOT_MODEL", "kimi-test")
    monkeypatch.setenv("MOONSHOT_BASE_URL", "https://example.com/v1")

    model = create_langchain_moonshot()

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "kimi-test"
    assert str(model.openai_api_base).rstrip("/") == "https://example.com/v1"


def test_create_langchain_moonshot_requires_api_key(
    monkeypatch,
):
    monkeypatch.setenv("MOONSHOT_API_KEY", "")

    try:
        create_langchain_moonshot()
    except ValueError as exc:
        assert "MOONSHOT_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing API key to raise ValueError")
