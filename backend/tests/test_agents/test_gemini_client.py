import src.agents.gemini_client as gemini_client
from src.agents.gemini_client import call_gemini


def test_returns_gemini_text_when_gemini_succeeds(monkeypatch):
    monkeypatch.setattr(gemini_client, "_call_gemini_raw", lambda prompt: "gemini answer")
    monkeypatch.setattr(
        gemini_client,
        "_call_openrouter_fallback",
        lambda prompt: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    result = call_gemini("hello")

    assert result == "gemini answer"


def test_falls_back_to_openrouter_when_gemini_fails(monkeypatch):
    monkeypatch.setattr(gemini_client, "_call_gemini_raw", lambda prompt: None)
    monkeypatch.setattr(gemini_client, "_call_openrouter_fallback", lambda prompt: "openrouter answer")

    result = call_gemini("hello")

    assert result == "openrouter answer"


def test_returns_none_when_both_providers_fail(monkeypatch):
    monkeypatch.setattr(gemini_client, "_call_gemini_raw", lambda prompt: None)
    monkeypatch.setattr(gemini_client, "_call_openrouter_fallback", lambda prompt: None)

    result = call_gemini("hello")

    assert result is None


def test_expect_json_extracts_fenced_json_from_openrouter_fallback(monkeypatch):
    monkeypatch.setattr(gemini_client, "_call_gemini_raw", lambda prompt: None)
    monkeypatch.setattr(
        gemini_client,
        "_call_openrouter_fallback",
        lambda prompt: 'Here you go:\n```json\n{"confidence": 80}\n```',
    )

    result = call_gemini("hello", expect_json=True)

    assert result == '{"confidence": 80}'


def test_expect_json_extracts_fenced_json_from_gemini(monkeypatch):
    monkeypatch.setattr(
        gemini_client,
        "_call_gemini_raw",
        lambda prompt: 'Here you go:\n```json\n{"confidence": 80}\n```',
    )
    monkeypatch.setattr(
        gemini_client,
        "_call_openrouter_fallback",
        lambda prompt: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    result = call_gemini("hello", expect_json=True)

    assert result == '{"confidence": 80}'
