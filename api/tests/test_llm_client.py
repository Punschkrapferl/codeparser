from unittest.mock import patch, AsyncMock
import httpx
import pytest

from api import llm_client


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
