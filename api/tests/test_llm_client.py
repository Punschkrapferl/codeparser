import pytest

from api import llm_client


@pytest.mark.asyncio
async def test_call_llm_dev_stub_basic() -> None:
    prompt = "Hello test prompt"

    result = await llm_client.call_llm(prompt)

    # Basic type/length checks
    assert isinstance(result, str)
    assert len(result) > 0

    # It should clearly be the DEV stub
    assert "DEV STUB ANALYSIS (no real LLM call)" in result
    assert "This response is generated instantly for fast testing." in result

    # It should echo configuration from the module
    assert f"Model configured: {llm_client.MODEL_NAME}" in result
    assert f"Ollama host    : {llm_client.OLLAMA_HOST}" in result

    # It should mention prompt length
    assert f"Prompt length  : {len(prompt)} characters" in result

    # It should include a preview of the prompt
    assert "Prompt preview :" in result
    assert "Hello test prompt" in result


@pytest.mark.asyncio
async def test_call_llm_dev_stub_truncates_preview() -> None:
    # Build a long prompt to ensure truncation logic is exercised
    long_prompt = "X" * 500  # > 400

    result = await llm_client.call_llm(long_prompt)

    # Preview should end with "..." when truncated
    assert "Prompt preview :" in result
    # Extract the preview line
    lines = [line for line in result.splitlines() if line.startswith("- Prompt preview")]
    assert len(lines) == 1
    preview_line = lines[0]

    # The preview should be shorter than the full prompt and end with "..."
    assert len(preview_line) < len(long_prompt) + 40  # some margin
    assert preview_line.rstrip().endswith("...")
