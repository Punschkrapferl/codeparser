from unittest.mock import patch, AsyncMock
import httpx
import pytest

from api import llm_client

# # Tests stub
# @pytest.mark.asyncio
# async def test_call_llm_stub_includes_basic_markers(monkeypatch) -> None:
#     # Make sure we control model + host in the output
#     monkeypatch.setattr(llm_client, "MODEL_NAME", "test-model")
#     monkeypatch.setattr(llm_client, "OLLAMA_HOST", "http://example-host")
#
#     prompt = "hello world"
#     result = await llm_client.call_llm(prompt)
#
#     # Core stub markers
#     assert "DEV STUB ANALYSIS (no real LLM call)" in result
#     assert "This response is generated instantly for fast testing." in result
#
#     # Config echo
#     assert "- Model configured: test-model" in result
#     assert "- Ollama host    : http://example-host" in result
#
#     # Length + preview based on the prompt
#     assert "- Prompt length  : 11 characters" in result
#     assert "- Prompt preview : hello world" in result
#
#
# @pytest.mark.asyncio
# async def test_call_llm_stub_truncates_preview_for_long_prompt(monkeypatch) -> None:
#     monkeypatch.setattr(llm_client, "MODEL_NAME", "m-long")
#     monkeypatch.setattr(llm_client, "OLLAMA_HOST", "http://h-long")
#
#     long_prompt = "x" * 1000
#     result = await llm_client.call_llm(long_prompt)
#
#     # Length reflects full prompt
#     assert "- Prompt length  : 1000 characters" in result
#
#     # Preview must be truncated and suffixed with "..."
#     # We do not assert the exact 400 chars, only that "..." is present
#     # and that we have a long run of x's.
#     assert "Prompt preview :" in result
#     assert "..." in result
#     assert "x" * 100 in result  # coarse sanity check that preview contains content
#
#
# @pytest.mark.asyncio
# async def test_call_llm_stub_does_not_raise_on_empty_prompt(monkeypatch) -> None:
#     monkeypatch.setattr(llm_client, "MODEL_NAME", "empty-test")
#     monkeypatch.setattr(llm_client, "OLLAMA_HOST", "http://empty-host")
#
#     result = await llm_client.call_llm("")
#
#     # Length 0
#     assert "- Prompt length  : 0 characters" in result
#     # Preview for empty prompt is just empty (no error)
#     assert "- Prompt preview : " in result

@pytest.mark.asyncio
async def test_call_llm_success_message_content():
    """200 OK, JSON has message.content -> return that."""
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"message": {"content": "response text"}}

        mock_client.post.return_value = mock_resp

        result = await llm_client.call_llm(prompt)

    assert result == "response text"


@pytest.mark.asyncio
async def test_call_llm_success_fallback_response_field():
    """200 OK, no message.content but has response -> use response."""
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"response": "fallback text"}

        mock_client.post.return_value = mock_resp

        result = await llm_client.call_llm(prompt)

    assert result == "fallback text"


@pytest.mark.asyncio
async def test_call_llm_success_awaitable_json():
    """
    200 OK, resp.json() returns an awaitable.
    Exercises the 'if callable(getattr(data, "__await__", None))' branch.
    """
    prompt = "Hello awaitable JSON"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        async_json = AsyncMock(return_value={"message": {"content": "async text"}})

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json = async_json

        mock_client.post.return_value = mock_resp

        result = await llm_client.call_llm(prompt)

    assert result == "async text"
    async_json.assert_awaited()


@pytest.mark.asyncio
async def test_call_llm_http_error_returns_error_string():
    """Non-2xx status -> error string starting with [LLM HTTP error ...]."""
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_resp = AsyncMock()
        mock_resp.status_code = 502
        mock_resp.text = "Bad Gateway"
        mock_resp.json.return_value = {}

        mock_client.post.return_value = mock_resp

        result = await llm_client.call_llm(prompt)

    assert isinstance(result, str)
    assert result.startswith("[LLM HTTP error 502]")
    assert "Bad Gateway" in result


@pytest.mark.asyncio
async def test_call_llm_request_error_returns_error_string():
    """httpx.RequestError -> '[LLM request error] ...' string."""
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        dummy_request = httpx.Request("POST", f"{llm_client.OLLAMA_HOST}/api/chat")
        mock_client.post.side_effect = httpx.RequestError(
            "Request failed", request=dummy_request
        )

        result = await llm_client.call_llm(prompt)

    assert isinstance(result, str)
    assert result.startswith("[LLM request error]")
    assert "Request failed" in result
    assert llm_client.OLLAMA_HOST in result


@pytest.mark.asyncio
async def test_call_llm_json_decode_error_returns_error_string():
    """JSON parsing error -> '[LLM JSON error] ...' string."""
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = "not valid json"
        mock_resp.json.side_effect = ValueError("Invalid JSON")

        mock_client.post.return_value = mock_resp

        result = await llm_client.call_llm(prompt)

    assert isinstance(result, str)
    assert result.startswith("[LLM JSON error]")
    assert "Invalid JSON" in result


@pytest.mark.asyncio
async def test_call_llm_missing_content_returns_error_string():
    """JSON OK but no message.content/response -> '[LLM error] Response missing usable content...'."""
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"message": {}}

        mock_client.post.return_value = mock_resp

        result = await llm_client.call_llm(prompt)

    assert isinstance(result, str)
    assert result == "[LLM error] Response missing usable content from Ollama."
