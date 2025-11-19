import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import logging

from api.hand_to_api import send_to_api

# --- Fixture for a temp file ---
@pytest.fixture
def sample_file(tmp_path):
    f = tmp_path / "test.jsonl"
    f.write_text('[{"path":"a.py","language":"python","code":"print(1)"}]')
    return f

# --- Async test for send_to_api ---
@pytest.mark.asyncio
async def test_send_to_api_calls_httpx_post(sample_file, caplog):
    caplog.set_level(logging.INFO)

    # Patch AsyncClient and its post method
    with patch("api.hand_to_api.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Simulate response object
        mock_response = MagicMock()
        mock_response.text = '{"analysis": "ok"}'
        mock_response.raise_for_status = MagicMock(return_value=None)  # synchronous
        mock_client.post.return_value = mock_response

        await send_to_api(sample_file)

        # Assert post called once with correct params
        mock_client.post.assert_awaited_once()
        args, kwargs = mock_client.post.call_args
        assert "files" in kwargs
        file_tuple = kwargs["files"]["file"]
        assert file_tuple[0] == sample_file.name

        # Check that logging occurred
        assert any("API response" in rec.message for rec in caplog.records)
