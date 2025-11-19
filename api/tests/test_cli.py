import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path
from api.cli import process_repo

@pytest.mark.asyncio
async def test_process_repo_fast(monkeypatch, tmp_path, capsys):
    # 1. Mock input
    monkeypatch.setattr("builtins.input", lambda _: "https://fake.repo/url.git")

    # 2. Mock clone_or_update
    fake_repo_path = tmp_path / "fake_repo"
    fake_repo_path.mkdir()
    monkeypatch.setattr("api.cli.clone_or_update", lambda url, path: str(fake_repo_path))

    # 3. Create parser_dir and a Go file
    parser_dir = tmp_path / "parser_go"
    parser_dir.mkdir()
    go_file = parser_dir / "main.go"
    go_file.write_text("package main\nfunc main() {}")

    # 4. Patch subprocess.run to do nothing
    with patch("api.cli.subprocess.run") as mock_run:
        mock_run.return_value = None

        # 5. Patch OUTPUT_JSONL
        fake_jsonl = tmp_path / "output.jsonl"
        fake_jsonl.write_text('[{"chunk": "data"}]')
        monkeypatch.setattr("api.cli.OUTPUT_JSONL", fake_jsonl)

        # 6. Patch LLM helpers
        monkeypatch.setattr("api.cli._parse_chunks_bytes", lambda raw: ["parsed"])
        monkeypatch.setattr("api.cli._normalize_chunks", lambda chunks: ["normalized"])
        monkeypatch.setattr("api.cli._analyze_parts", AsyncMock(return_value={"analysis": "ok"}))

        # 7. Patch parser_dir assignment inside process_repo
        class PatchedPath(Path):
            def __truediv__(self, key):
                result = super().__truediv__(key)
                if str(result).endswith("parser_go"):
                    return parser_dir
                return result

            @property
            def parent(self):
                return self

        monkeypatch.setattr("api.cli.Path", PatchedPath)

        # 8. Run process_repo
        await process_repo()

    captured = capsys.readouterr()
    assert "Fetching repo..." in captured.out
    assert "Running Go parser..." in captured.out
    assert "Sending parsed chunks to LLM..." in captured.out
    assert "ok" in captured.out
