import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from typing import cast
from httpx import Request, Response, HTTPStatusError, RequestError

from api.llm_client import call_llm

@pytest.mark.asyncio
async def test_call_llm_success_async_json():
    prompt = "Hello LLM"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # async .json() mock
        async def async_json():
            return {"message": {"content": "response text"}}

        mock_response = AsyncMock()
        mock_response.json = AsyncMock(side_effect=async_json)
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response

        result = await call_llm(prompt)
        assert result == "response text"


@pytest.mark.asyncio
async def test_call_llm_http_status_error():
    prompt = "Hello"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        dummy_request = Request("POST", "http://localhost:11434/api/chat")
        dummy_response = Response(502, request=dummy_request, text="Bad Gateway")

        mock_client.post.side_effect = HTTPStatusError(
            "HTTP error", request=dummy_request, response=dummy_response
        )

        with pytest.raises(HTTPException) as exc:
            await call_llm(prompt)

        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 502
        assert "Ollama HTTP" in getattr(http_exc, "detail", "")
        assert "Bad Gateway" in getattr(http_exc, "detail", "")

@pytest.mark.asyncio
async def test_call_llm_request_error():
    prompt = "Hello"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        dummy_request = Request("POST", "http://localhost:11434/api/chat")
        mock_client.post.side_effect = RequestError("Request failed", request=dummy_request)

        with pytest.raises(HTTPException) as exc:
            await call_llm(prompt)

        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 502
        assert "Ollama request error" in getattr(http_exc, "detail", "")

@pytest.mark.asyncio
async def test_call_llm_json_decode_error():
    prompt = "Hello"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.post.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            await call_llm(prompt)

        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 502
        assert "Ollama JSON decode error" in getattr(http_exc, "detail", "")

@pytest.mark.asyncio
async def test_call_llm_missing_content():
    prompt = "Hello"

    with patch("api.llm_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.json.return_value = {"message": {}}
        mock_client.post.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            await call_llm(prompt)

        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 502
        assert "Ollama response missing message.content" in getattr(http_exc, "detail", "")
