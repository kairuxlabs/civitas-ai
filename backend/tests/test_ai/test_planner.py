import pytest
from unittest.mock import AsyncMock, patch

from src.ai.planner import complete


@pytest.mark.asyncio
async def test_returns_none_when_pre_check_unsafe():
    mock_gateway = AsyncMock(return_value={"choices": [{"message": {"content": "text"}}]})
    with patch(
        "src.ai.planner.check_safety",
        new=AsyncMock(return_value={"safe": False, "reason": "unsafe: threat"}),
    ), patch("src.ai.planner.call_openrouter", new=mock_gateway):
        result = await complete("dangerous prompt")

    assert result is None
    mock_gateway.assert_not_called()


@pytest.mark.asyncio
async def test_returns_text_when_pre_and_post_checks_safe_and_gateway_succeeds():
    mock_safety = AsyncMock(return_value={"safe": True, "reason": None})
    with patch("src.ai.planner.check_safety", new=mock_safety), patch(
        "src.ai.planner.call_openrouter",
        new=AsyncMock(return_value={"choices": [{"message": {"content": "the plan"}}]}),
    ):
        result = await complete("prompt", context="some context")

    assert result == "the plan"
    assert mock_safety.await_count == 2
    mock_safety.assert_any_await("prompt")
    mock_safety.assert_any_await("the plan")


@pytest.mark.asyncio
async def test_returns_none_when_post_check_unsafe():
    mock_safety = AsyncMock(
        side_effect=[
            {"safe": True, "reason": None},
            {"safe": False, "reason": "unsafe: flagged output"},
        ]
    )
    with patch("src.ai.planner.check_safety", new=mock_safety), patch(
        "src.ai.planner.call_openrouter",
        new=AsyncMock(return_value={"choices": [{"message": {"content": "bad output"}}]}),
    ):
        result = await complete("prompt")

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_gateway_returns_none():
    with patch(
        "src.ai.planner.check_safety",
        new=AsyncMock(return_value={"safe": True, "reason": None}),
    ), patch("src.ai.planner.call_openrouter", new=AsyncMock(return_value=None)):
        result = await complete("prompt")

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_when_gateway_response_malformed():
    mock_safety = AsyncMock(return_value={"safe": True, "reason": None})
    with patch("src.ai.planner.check_safety", new=mock_safety), patch(
        "src.ai.planner.call_openrouter",
        new=AsyncMock(return_value={"choices": []}),
    ):
        result = await complete("prompt")

    assert result is None
    # post-check should never run because there is no text to check
    assert mock_safety.await_count == 1


@pytest.mark.asyncio
async def test_returns_none_when_gateway_response_is_not_a_dict_shape():
    mock_safety = AsyncMock(return_value={"safe": True, "reason": None})
    with patch("src.ai.planner.check_safety", new=mock_safety), patch(
        "src.ai.planner.call_openrouter",
        new=AsyncMock(return_value={"choices": [{"message": None}]}),
    ):
        result = await complete("prompt")

    assert result is None
    assert mock_safety.await_count == 1


@pytest.mark.asyncio
async def test_returns_none_when_gateway_response_missing_choices_key():
    mock_safety = AsyncMock(return_value={"safe": True, "reason": None})
    with patch("src.ai.planner.check_safety", new=mock_safety), patch(
        "src.ai.planner.call_openrouter",
        new=AsyncMock(return_value={}),
    ):
        result = await complete("prompt")

    assert result is None
    assert mock_safety.await_count == 1


@pytest.mark.asyncio
async def test_builds_full_prompt_with_context_prefix():
    mock_gateway = AsyncMock(return_value={"choices": [{"message": {"content": "reply"}}]})
    with patch(
        "src.ai.planner.check_safety",
        new=AsyncMock(return_value={"safe": True, "reason": None}),
    ), patch("src.ai.planner.call_openrouter", new=mock_gateway):
        await complete("do the thing", context="background info")

    sent_payload = mock_gateway.call_args.args[1]
    assert sent_payload["messages"][0]["content"] == "background info\n\ndo the thing"


@pytest.mark.asyncio
async def test_builds_prompt_without_context_when_context_empty():
    mock_gateway = AsyncMock(return_value={"choices": [{"message": {"content": "reply"}}]})
    with patch(
        "src.ai.planner.check_safety",
        new=AsyncMock(return_value={"safe": True, "reason": None}),
    ), patch("src.ai.planner.call_openrouter", new=mock_gateway):
        await complete("do the thing")

    sent_payload = mock_gateway.call_args.args[1]
    assert sent_payload["messages"][0]["content"] == "do the thing"
