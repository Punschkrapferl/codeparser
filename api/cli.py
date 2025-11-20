import asyncio
import logging
import subprocess
from pathlib import Path

from api.github_client import clone_or_update
from api.api_main import OUTPUT_JSONL
from api.helpers import _normalize_chunks, _parse_chunks_bytes, _analyze_parts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_repo(parser_root: Path | None = None) -> None:
    """
    Small CLI helper to:
    - ask for a GitHub URL
    - clone/update the repo
    - run the Go parser
    - send parsed chunks to the LLM
    - print the analysis

    parser_root:
        Optional root directory for locating parser_go/.
        Defaults to project root (two levels above this file).
        Tests can pass a temporary directory here.
    """
    repo_url = input("Enter GitHub repo URL: ").strip()
    if not repo_url:
        print("Repo URL required")
        return

    print("Fetching repo...")
    repo_path = clone_or_update(repo_url, Path("repos"))

    # Determine where parser_go lives
    if parser_root is None:
        root = Path(__file__).resolve().parent.parent
    else:
        root = Path(parser_root)

    parser_dir = root / "parser_go"
    logger.info("Using parser_dir=%s", parser_dir)

    # gather all Go files except *_test.go
    go_files = [str(f) for f in parser_dir.glob("*.go") if not f.name.endswith("_test.go")]

    if not go_files:
        print("No Go files found to run.")
        return

    # build the command
    repo_path = Path(repo_path)
    cmd = ["go", "run", *go_files, str(repo_path.resolve())]

    print("Running Go parser...")
    try:
        subprocess.run(
            cmd,
            cwd=parser_dir,
            check=True,
            capture_output=True,
            text=True,
        )
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
