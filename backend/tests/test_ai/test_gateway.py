import asyncio
import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.gateway import call_openrouter


@pytest.mark.asyncio
async def test_returns_none_when_api_key_unset(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "")
    result = await call_openrouter(["model-a"], {"messages": []})
    assert result is None


@pytest.mark.asyncio
async def test_returns_first_successful_response(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "test-key")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"choices": [{"message": {"content": "hi"}}]})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("src.ai.gateway.aiohttp.ClientSession", return_value=mock_session):
        result = await call_openrouter(["model-a"], {"messages": []})

    assert result == {"choices": [{"message": {"content": "hi"}}]}


@pytest.mark.asyncio
async def test_falls_back_to_next_model_on_failure(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "test-key")

    fail_resp = MagicMock()
    fail_resp.status = 500
    fail_resp.json = AsyncMock(return_value={"error": "fail"})
    fail_resp.__aenter__ = AsyncMock(return_value=fail_resp)
    fail_resp.__aexit__ = AsyncMock(return_value=None)

    ok_resp = MagicMock()
    ok_resp.status = 200
    ok_resp.json = AsyncMock(return_value={"choices": [{"message": {"content": "ok"}}]})
    ok_resp.__aenter__ = AsyncMock(return_value=ok_resp)
    ok_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=[fail_resp, ok_resp])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("src.ai.gateway.aiohttp.ClientSession", return_value=mock_session):
        result = await call_openrouter(["model-a", "model-b"], {"messages": []})

    assert result == {"choices": [{"message": {"content": "ok"}}]}


@pytest.mark.asyncio
async def test_returns_none_when_all_models_fail(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "test-key")

    with patch("src.ai.gateway.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=RuntimeError("network down"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        result = await call_openrouter(["model-a", "model-b"], {"messages": []})

    assert result is None


@pytest.mark.asyncio
async def test_uses_configured_timeout(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("src.utils.config.settings.openrouter_timeout_seconds", 7.5)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"choices": [{"message": {"content": "hi"}}]})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("src.ai.gateway.aiohttp.ClientSession", return_value=mock_session) as mock_ctor:
        await call_openrouter(["model-a"], {"messages": []})

    _, kwargs = mock_ctor.call_args
    assert isinstance(kwargs["timeout"], aiohttp.ClientTimeout)
    assert kwargs["timeout"].total == 7.5


@pytest.mark.asyncio
async def test_timeout_error_falls_back_to_next_model(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "test-key")

    ok_resp = MagicMock()
    ok_resp.status = 200
    ok_resp.json = AsyncMock(return_value={"choices": [{"message": {"content": "ok"}}]})
    ok_resp.__aenter__ = AsyncMock(return_value=ok_resp)
    ok_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=[asyncio.TimeoutError(), ok_resp])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("src.ai.gateway.aiohttp.ClientSession", return_value=mock_session):
        result = await call_openrouter(["model-a", "model-b"], {"messages": []})

    assert result == {"choices": [{"message": {"content": "ok"}}]}
