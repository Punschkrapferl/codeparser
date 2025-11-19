from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os, math, asyncio, json, subprocess, logging
from pydantic import BaseModel

from api.github_client import clone_or_update
from api.llm_client import call_llm

# ------------ config ------------
logging.basicConfig(level=logging.INFO)
APP_DIR       = Path(__file__).resolve().parent
PROJECT_ROOT  = APP_DIR.parent
REPOS_DIR     = Path(os.getenv("REPOS_DIR", APP_DIR / "repos")).resolve()
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME    = os.getenv("MODEL_NAME", "mistral:latest")
BATCH_SIZE    = int(os.getenv("BATCH_SIZE", "4"))
OUTPUT_JSONL = Path("api/output.jsonl")  # default location

app = FastAPI(title="CodeParser + Local LLM")

# ---------- helpers ----------
def _parse_chunks_bytes(raw: bytes) -> List[Dict[str, Any]]:
    t = raw.decode("utf-8", errors="ignore").strip()
    if not t:
        return []
    try:
        arr = json.loads(t)
        if isinstance(arr, list):
            return arr
    except json.JSONDecodeError:
        pass
    items: List[Dict[str, Any]] = []
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            items.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return items

def _normalize_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    parts: List[Dict[str, str]] = []
    for c in chunks:
        path = c.get("path", "<unknown>")
        lang = c.get("language", c.get("Language", "<unknown>"))
        code = c.get("code") or c.get("Code") or ""
        if code:
            parts.append({"path": path, "language": lang, "code": code})
    return parts

async def _analyze_parts(parts: List[Dict[str, str]], system_hint: Optional[str] = None) -> Dict[str, Any]:
    if not parts:
        return {"analysis": "", "batches": 0}
    results: List[Dict[str, Any]] = []
    n_batches = math.ceil(len(parts) / BATCH_SIZE)
    for i in range(n_batches):
        batch = parts[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        segs: List[str] = []
        if system_hint:
            segs.append(f"[Context]\n{system_hint}\n")
        segs.append("For each file, output purpose, key APIs, risks, and fixes.\n")

        for it in batch:
            segs.append(f"---\nFile: {it['path']} ({it['language']})\n{it['code']}\n")

        analysis = await call_llm("\n".join(segs))
        results.append({"batch": i, "analysis": analysis})
        if i < n_batches - 1:
            await asyncio.sleep(0.25)
    return {"analysis": "\n\n".join(r["analysis"] for r in results), "batches": len(results)}

# ------------ models ------------
class AnalyzeIn(BaseModel):
    repo_url: str
    system_hint: str | None = None

# ---------- routes ----------
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
async def analyze_code(file: UploadFile = File(...), system_hint: Optional[str] = Query(None)):
    raw = await file.read()
    parts = _normalize_chunks(_parse_chunks_bytes(raw))
    out = await _analyze_parts(parts, system_hint)
    return JSONResponse(out)

@app.post("/github/pull")
def github_pull(repo_url: str = Query(..., min_length=5)):
    path = clone_or_update(repo_url, REPOS_DIR)
    return {"repo_path": path}

@app.post("/github/parse")
def github_parse(repo_path: str = Query(..., min_length=1)):
    repo = Path(repo_path).resolve()
    if not repo.exists():
        raise HTTPException(status_code=400, detail="repo_path not found")

    root = Path(__file__).resolve().parents[1]
    parser_dir = root / "parser_go"

    # Collect all non-test go files
    go_files = [
        str(p)
        for p in parser_dir.glob("*.go")
        if not p.name.endswith("_test.go")
    ]
    if not go_files:
        raise HTTPException(status_code=500, detail="No parser_go source files found")

    # Build full command: go run <files> <repo>
    cmd = ["go", "run", *go_files, str(repo)]

    try:
        subprocess.run(
            cmd,
            cwd=root,
            check=True,
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Go toolchain not found")
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        raise HTTPException(status_code=500, detail=f"go run error: {err}")

    # Output location (always PROJECT_ROOT/api/output.jsonl)
    output_jsonl = root / "api" / "output.jsonl"
    if not output_jsonl.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Expected output at {output_jsonl}, but file does not exist"
        )

    return {
        "output_jsonl": str(output_jsonl),
        "repo_path": str(repo)
    }



@app.post("/github/analyze")
async def github_analyze(
        request: Request,
        repo_url: Optional[str] = Query(None),
        system_hint: Optional[str] = Query(None),
):
    # Parse JSON body optionally
    body_repo = None
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                body_repo = payload.get("repo_url")
                if payload.get("system_hint") and not system_hint:
                    system_hint = str(payload["system_hint"])
        except Exception:
            pass

    repo_url = repo_url or body_repo
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url required")

    # Clone or pull repo
    repo_path = Path(clone_or_update(repo_url, REPOS_DIR))

    # Root for parser and output
    root = Path(__file__).resolve().parents[1]
    parser_dir = root / "parser_go"

    # Collect Go source files (exclude tests)
    go_files = [
        str(p)
        for p in parser_dir.glob("*.go")
        if not p.name.endswith("_test.go")
    ]
    if not go_files:
        raise HTTPException(status_code=500, detail="No parser_go source files found")

    cmd = ["go", "run", *go_files, str(repo_path)]

    try:
        subprocess.run(
            cmd,
            cwd=root,
            check=True,
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Go toolchain not found")
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        raise HTTPException(status_code=500, detail=f"go run error: {err}")

    # Output always written here
    output_jsonl = root / "api" / "output.jsonl"
    try:
        raw = output_jsonl.read_bytes()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"cannot read output file: {e}")

    parts = _normalize_chunks(_parse_chunks_bytes(raw))
    out = await _analyze_parts(parts, system_hint)

    return {
        **out,
        "repo_path": str(repo_path),
        "source_file": str(output_jsonl)
    }

