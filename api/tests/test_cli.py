import pytest
from unittest.mock import AsyncMock, patch

from api.cli import process_repo


@pytest.mark.asyncio
async def test_process_repo_fast(monkeypatch, tmp_path, capsys):
    # 1. Mock input() to provide a fake repo URL
    monkeypatch.setattr("builtins.input", lambda _: "https://fake.repo/url.git")

    # 2. Mock clone_or_update to return a fake repo path
    fake_repo_path = tmp_path / "fake_repo"
    fake_repo_path.mkdir()
    monkeypatch.setattr(
        "api.cli.clone_or_update",
        lambda url, dest: str(fake_repo_path),
    )

    # 3. Create parser_dir and a dummy Go file under parser_root
    parser_dir = tmp_path / "parser_go"
    parser_dir.mkdir()
    go_file = parser_dir / "main.go"
    go_file.write_text("package main\nfunc main() {}", encoding="utf-8")

    # 4. Patch subprocess.run so we don't run a real Go toolchain
    with patch("api.cli.subprocess.run") as mock_run:
        mock_run.return_value = None

        # 5. Patch OUTPUT_JSONL to point to a fake JSONL file
        fake_jsonl = tmp_path / "output.jsonl"
        fake_jsonl.write_text('[{"path": "a.py", "language": "python", "code": "print(1)"}]', encoding="utf-8")
        monkeypatch.setattr("api.cli.OUTPUT_JSONL", fake_jsonl)

        # 6. Patch helper functions in the cli module namespace
        monkeypatch.setattr("api.cli._parse_chunks_bytes", lambda raw: [{"path": "a.py", "language": "python", "code": "print(1)"}])
        monkeypatch.setattr("api.cli._normalize_chunks", lambda chunks: chunks)
        monkeypatch.setattr("api.cli._analyze_parts", AsyncMock(return_value={"analysis": "ok", "batches": 1}))

        # 7. Run process_repo with parser_root pointing to tmp_path
        await process_repo(parser_root=tmp_path)

    captured = capsys.readouterr()
    assert "Fetching repo..." in captured.out
    assert "Running Go parser..." in captured.out
    assert "Sending parsed chunks to LLM..." in captured.out
    assert "\n--- Analysis ---\n" in captured.out
    assert "ok" in captured.out
