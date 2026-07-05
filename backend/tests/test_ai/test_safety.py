import pytest
from unittest.mock import AsyncMock, patch

from src.ai.safety import check_safety


@pytest.mark.asyncio
async def test_returns_safe_when_gateway_reports_safe():
    with patch(
        "src.ai.safety.call_openrouter",
        new=AsyncMock(return_value={"choices": [{"message": {"content": "Safe"}}]}),
    ):
        result = await check_safety("hello world")

    assert result == {"safe": True, "reason": None}


@pytest.mark.asyncio
async def test_returns_unsafe_with_reason_when_gateway_flags_content():
    with patch(
        "src.ai.safety.call_openrouter",
        new=AsyncMock(
            return_value={"choices": [{"message": {"content": "Unsafe: contains threats"}}]}
        ),
    ):
        result = await check_safety("some threatening text")

    assert result == {"safe": False, "reason": "unsafe: contains threats"}


@pytest.mark.asyncio
async def test_fails_open_when_gateway_returns_none():
    with patch("src.ai.safety.call_openrouter", new=AsyncMock(return_value=None)):
        result = await check_safety("anything")

    assert result == {"safe": True, "reason": None}


@pytest.mark.asyncio
async def test_fails_open_when_gateway_returns_malformed_shape():
    with patch(
        "src.ai.safety.call_openrouter",
        new=AsyncMock(return_value={"choices": []}),
    ):
        result = await check_safety("anything")

    assert result == {"safe": True, "reason": None}
