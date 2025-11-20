import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.hand_to_api import send_to_api


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.jsonl"
    f.write_text('[{"path":"a.py","language":"python","code":"print(1)"}]', encoding="utf-8")
    return f


@pytest.mark.asyncio
async def test_send_to_api_calls_httpx_post(sample_file: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)

    # Patch AsyncClient where it is used: api.hand_to_api.httpx.AsyncClient
    with patch("api.hand_to_api.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        # __aenter__ of the context manager returns our mock client
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Fake response
        mock_response = MagicMock()
        mock_response.text = '{"analysis": "ok"}'
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response

        # Call function under test
        await send_to_api(sample_file)

        # Assert HTTP call
        mock_client.post.assert_awaited_once()
        args, kwargs = mock_client.post.call_args

        # Optionally assert URL
        assert args[0] == "http://localhost:8000/analyze"

        # Assert file payload
        assert "files" in kwargs
        file_tuple = kwargs["files"]["file"]
        assert file_tuple[0] == sample_file.name  # filename

        # Assert logging
        assert any("API response" in rec.message for rec in caplog.records)
