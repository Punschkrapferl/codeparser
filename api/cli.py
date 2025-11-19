import asyncio
import logging
from pathlib import Path
from api.github_client import clone_or_update
import subprocess
from api.api_main import _normalize_chunks, _parse_chunks_bytes, _analyze_parts, OUTPUT_JSONL

logging.basicConfig(level=logging.INFO)

async def process_repo():
    repo_url = input("Enter GitHub repo URL: ").strip()
    if not repo_url:
        print("Repo URL required")
        return

    print("Fetching repo...")
    repo_path = clone_or_update(repo_url, Path("repos"))

    print("Running Go parser...")
    root = Path(__file__).resolve().parent.parent
    parser_dir = root / "parser_go"

    # gather all Go files except *_test.go
    go_files = [str(f) for f in parser_dir.glob("*.go") if not f.name.endswith("_test.go")]

    if not go_files:
        print("No Go files found to run.")
        return

    # build the command
    repo_path = Path(repo_path)  # convert string to Path
    cmd = ["go", "run", *go_files, str(repo_path.resolve())]

    try:
        subprocess.run(cmd, cwd=parser_dir, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Go toolchain not found")
        return
    except subprocess.CalledProcessError as e:
        print(f"Parser error:\n{(e.stderr or e.stdout)}")
        return

    if not OUTPUT_JSONL.exists():
        print(f"Expected {OUTPUT_JSONL} not found")
        return

    print("Sending parsed chunks to LLM...")
    raw = OUTPUT_JSONL.read_bytes()
    parts = _normalize_chunks(_parse_chunks_bytes(raw))
    analysis = await _analyze_parts(parts)

    print("\n--- Analysis ---\n")
    print(analysis["analysis"])

if __name__ == "__main__":
    asyncio.run(process_repo())
