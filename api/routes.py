import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Query,
    HTTPException,
    Request,
)

from api.api_main import REPOS_DIR, PROJECT_ROOT, OUTPUT_JSONL
from api.github_client import clone_or_update
from api.helpers import _parse_chunks_bytes, _normalize_chunks, _analyze_parts

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/analyze")
async def analyze_code(
        file: UploadFile = File(...),
        system_hint: Optional[str] = Query(None),
):
    raw = await file.read()
    logging.info("POST /analyze file=%r size=%d", file.filename, len(raw))

    chunks = _parse_chunks_bytes(raw, filename=file.filename)
    parts = _normalize_chunks(chunks)

    out = await _analyze_parts(parts, system_hint)

    languages = sorted({p["language"] for p in parts}) if parts else []

    return {
        "analysis": out.get("analysis", ""),
        "batches": out.get("batches", 0),
        "num_parts": len(parts),
        "filename": file.filename,
        "languages": languages,
    }


@router.post("/analyze-multi")
async def analyze_multi(
        files: List[UploadFile] = File(...),
        system_hint: Optional[str] = Query(None),
):
    """
    Analyse multiple uploaded files at once (e.g. a folder).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    all_parts: List[Dict[str, str]] = []
    file_summaries: List[Dict[str, Any]] = []

    for f in files:
        raw = await f.read()
        logging.info("POST /analyze-multi: file=%r size=%d", f.filename, len(raw))

        chunks = _parse_chunks_bytes(raw, filename=f.filename)
        parts = _normalize_chunks(chunks)

        all_parts.extend(parts)
        file_summaries.append({
            "filename": f.filename,
            "num_parts": len(parts),
        })

    out = await _analyze_parts(all_parts, system_hint)
    languages = sorted({p["language"] for p in all_parts}) if all_parts else []

    return {
        "analysis": out.get("analysis", ""),
        "batches": out.get("batches", 0),
        "total_parts": len(all_parts),
        "num_files": len(files),
        "languages": languages,
        "file_summaries": file_summaries,
    }


@router.post("/github/pull")
def github_pull(repo_url: str = Query(..., min_length=5)):
    path = clone_or_update(repo_url, REPOS_DIR)
    return {"repo_path": path}


@router.post("/github/parse")
def github_parse(repo_path: str = Query(..., min_length=1)):
    repo = Path(repo_path).resolve()
    if not repo.exists():
        raise HTTPException(status_code=400, detail="repo_path not found")

    parser_dir = PROJECT_ROOT / "parser_go"

    go_files = [
        str(p)
        for p in parser_dir.glob("*.go")
        if not p.name.endswith("_test.go")
    ]
    if not go_files:
        raise HTTPException(
            status_code=500,
            detail="No parser_go source files found",
        )

    cmd = ["go", "run", *go_files, str(repo_path)]

    try:
        subprocess.run(
            cmd,
            cwd=parser_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Go toolchain not found")
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        raise HTTPException(status_code=500, detail=f"go run error: {err}")

    if not OUTPUT_JSONL.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Expected output at {OUTPUT_JSONL}, but file does not exist",
        )

    return {
        "output_jsonl": str(OUTPUT_JSONL),
        "repo_path": str(repo),
    }


@router.post("/github/analyze")
async def github_analyze(
        request: Request,
        repo_url: Optional[str] = Query(None),
        system_hint: Optional[str] = Query(None),
):
    """
    End-to-end: clone/pull repo, run Go parser, read output.jsonl,
    normalize chunks and call LLM.
    """
    body_repo: Optional[str] = None

    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            raw_payload = await request.json()
        except ValueError:
            raw_payload = None

        if isinstance(raw_payload, dict):
            payload = raw_payload
            body_repo = payload.get("repo_url")
            if payload.get("system_hint") and not system_hint:
                system_hint = str(payload["system_hint"])

    repo_url = repo_url or body_repo
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url required")

    repo_path = Path(clone_or_update(repo_url, REPOS_DIR))

    parser_dir = PROJECT_ROOT / "parser_go"
    go_files = [
        str(p)
        for p in parser_dir.glob("*.go")
        if not p.name.endswith("_test.go")
    ]
    if not go_files:
        raise HTTPException(
            status_code=500,
            detail="No parser_go source files found",
        )

    cmd = ["go", "run", *go_files, str(repo_path)]

    try:
        subprocess.run(
            cmd,
            cwd=parser_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Go toolchain not found")
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        raise HTTPException(status_code=500, detail=f"go run error: {err}")

    try:
        raw = OUTPUT_JSONL.read_bytes()
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"cannot read output file: {e}",
        )

    chunks = _parse_chunks_bytes(raw, filename=str(OUTPUT_JSONL.name))
    parts = _normalize_chunks(chunks)
    out = await _analyze_parts(parts, system_hint)

    languages = sorted({p["language"] for p in parts}) if parts else []

    return {
        **out,
        "repo_path": str(repo_path),
        "source_file": str(OUTPUT_JSONL),
        "num_parts": len(parts),
        "languages": languages,
    }
