from unittest.mock import AsyncMock

import pytest

from api import helpers


# ---------------------- _guess_language_from_name ----------------------


def test_guess_language_from_name_basic_extensions() -> None:
    assert helpers._guess_language_from_name("main.py") == "python"
    assert helpers._guess_language_from_name("App.java") == "java"
    assert helpers._guess_language_from_name("component.ts") == "typescript"
    assert helpers._guess_language_from_name("script.js") == "javascript"
    assert helpers._guess_language_from_name("server.go") == "go"
    assert helpers._guess_language_from_name("data.json") == "json"
    assert helpers._guess_language_from_name("README.md") == "text"
    assert helpers._guess_language_from_name("notes.txt") == "text"


def test_guess_language_from_name_binary_and_unknown() -> None:
    assert helpers._guess_language_from_name("movie.mp4") == "<binary>"
    assert helpers._guess_language_from_name("image.png") == "<binary>"
    assert helpers._guess_language_from_name("something.weirdext") == "<unknown>"
    assert helpers._guess_language_from_name(None) == "<unknown>"


# ---------------------- _parse_chunks_bytes ----------------------


def test_parse_chunks_bytes_empty() -> None:
    chunks = helpers._parse_chunks_bytes(b"", filename="empty.txt")
    assert chunks == []


def test_parse_chunks_bytes_json_array() -> None:
    raw = b'[{"path":"a.py","language":"python","code":"print(1)"}]'
    chunks = helpers._parse_chunks_bytes(raw, filename="a.py")
    assert isinstance(chunks, list)
    assert len(chunks) == 1
    assert chunks[0]["path"] == "a.py"
    assert chunks[0]["language"] == "python"
    assert chunks[0]["code"] == "print(1)"


def test_parse_chunks_bytes_jsonl() -> None:
    raw = (
        b'{"path":"a.py","language":"python","code":"print(1)"}\n'
        b'{"path":"b.java","language":"java","code":"class B {}"}\n'
    )
    chunks = helpers._parse_chunks_bytes(raw, filename="chunks.jsonl")
    assert len(chunks) == 2
    paths = {c["path"] for c in chunks}
    assert paths == {"a.py", "b.java"}


def test_parse_chunks_bytes_plain_text_fallback() -> None:
    content = b"def hello():\n    return 'world'\n"
    chunks = helpers._parse_chunks_bytes(content, filename="hello.py")
    assert len(chunks) == 1
    ch = chunks[0]
    assert ch["path"] == "hello.py"
    assert ch["language"] == "python"
    assert "def hello()" in ch["code"]


def test_parse_chunks_bytes_skips_binary() -> None:
    content = b"fake binary content"
    chunks = helpers._parse_chunks_bytes(content, filename="video.mp4")
    assert chunks == []  # extension treated as <binary>


# ---------------------- _normalize_chunks ----------------------


def test_normalize_chunks_basic_and_alt_keys() -> None:
    chunks = [
        {"path": "a.py", "language": "python", "code": "print('hi')"},
        {"Path": "b.java", "Language": "java", "Code": "class A {}"},
        {"path": "c.py", "language": "python", "code": ""},       # empty -> dropped
        {"path": "d.py", "language": "python", "code": None},     # None -> dropped
        {"path": "e.py", "language": "python", "code": 123},      # non-str -> dropped
    ]
    norm = helpers._normalize_chunks(chunks)
    assert len(norm) == 2

    paths = [c["path"] for c in norm]
    langs = {c["language"] for c in norm}

    # First item keeps its explicit path
    assert paths[0] == "a.py"
    # Second item has no "path" key, so -> "<unknown>"
    assert paths[1] == "<unknown>"

    # Language normalization still works (language / Language)
    assert langs == {"python", "java"}


# ---------------------- _analyze_parts ----------------------


@pytest.mark.asyncio
async def test_analyze_parts_empty_returns_zero_batches(monkeypatch) -> None:
    fake_llm = AsyncMock()
    monkeypatch.setattr(helpers, "call_llm", fake_llm)

    result = await helpers._analyze_parts([])
    assert result == {"analysis": "", "batches": 0}
    fake_llm.assert_not_awaited()


@pytest.mark.asyncio
async def test_analyze_parts_single_batch(monkeypatch) -> None:
    monkeypatch.setattr(helpers, "BATCH_SIZE", 10)

    fake_llm = AsyncMock(return_value="LLM-RESULT")
    monkeypatch.setattr(helpers, "call_llm", fake_llm)

    parts = [
        {"path": "a.py", "language": "python", "code": "print(1)"},
        {"path": "b.py", "language": "python", "code": "print(2)"},
    ]

    result = await helpers._analyze_parts(parts, system_hint="Use simple language")

    assert result["batches"] == 1
    assert "### Batch 1/1" in result["analysis"]
    assert "LLM-RESULT" in result["analysis"]

    fake_llm.assert_awaited_once()
    (prompt_arg,) = fake_llm.call_args.args
    assert "Use simple language" in prompt_arg
    assert "a.py" in prompt_arg
    assert "b.py" in prompt_arg


@pytest.mark.asyncio
async def test_analyze_parts_multiple_batches(monkeypatch) -> None:
    monkeypatch.setattr(helpers, "BATCH_SIZE", 2)

    fake_llm = AsyncMock(side_effect=["RES-1", "RES-2", "RES-3"])
    monkeypatch.setattr(helpers, "call_llm", fake_llm)

    parts = [
        {"path": f"file{i}.py", "language": "python", "code": f"print({i})"}
        for i in range(5)
    ]

    result = await helpers._analyze_parts(parts)

    assert result["batches"] == 3
    assert "### Batch 1/3" in result["analysis"]
    assert "### Batch 2/3" in result["analysis"]
    assert "### Batch 3/3" in result["analysis"]
    assert "RES-1" in result["analysis"]
    assert "RES-2" in result["analysis"]
    assert "RES-3" in result["analysis"]

    assert fake_llm.await_count == 3

    calls = fake_llm.call_args_list
    batch1_prompt = calls[0].args[0]
    batch2_prompt = calls[1].args[0]
    batch3_prompt = calls[2].args[0]

    assert "file0.py" in batch1_prompt and "file1.py" in batch1_prompt
    assert "file2.py" in batch2_prompt and "file3.py" in batch2_prompt
    assert "file4.py" in batch3_prompt
