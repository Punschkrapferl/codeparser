import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    Query,
    HTTPException,
    Request,
)

from api.api_main import REPOS_DIR, PROJECT_ROOT, OUTPUT_JSONL
from api.github_client import clone_or_update
from api.helpers import (
    _parse_chunks_bytes,
    _normalize_chunks,
    _analyze_parts,
    AnalyzeIn,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory job store for GitHub analysis jobs
JOBS: Dict[str, Dict[str, Any]] = {}


async def _run_github_pipeline(
        repo_url: str,
        system_hint: Optional[str],
) -> Dict[str, Any]:
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


@router.post("/github/analyze")
async def github_analyze(
        request: Request,
        repo_url: Optional[str] = Query(None),
        system_hint: Optional[str] = Query(None),
):
    """
    Synchronous, one-shot GitHub analysis.
    """
    body_repo: Optional[str] = None
    raw_payload = None

    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            raw_payload = await request.json()
        except ValueError:
            raw_payload = None

    if isinstance(raw_payload, dict):
        body_repo = raw_payload.get("repo_url")
        if raw_payload.get("system_hint") and not system_hint:
            system_hint = str(raw_payload["system_hint"])

    repo_url = repo_url or body_repo
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url required")

    return await _run_github_pipeline(repo_url, system_hint)


async def _github_job_worker(job_id: str, repo_url: str, system_hint: Optional[str]) -> None:
    JOBS[job_id]["status"] = "running"
    JOBS[job_id]["error"] = None
    try:
        result = await _run_github_pipeline(repo_url, system_hint)
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = result
    except HTTPException as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = f"{e.status_code}: {e.detail}"
    except Exception as e:
        logger.exception("GitHub job %s crashed", job_id)
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


@router.post("/analyze-github-job")
async def start_github_job(payload: AnalyzeIn):
    if not payload.repo_url or len(payload.repo_url) < 5:
        raise HTTPException(status_code=400, detail="repo_url invalid")

    job_id = str(uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
    }

    asyncio.create_task(_github_job_worker(job_id, payload.repo_url, payload.system_hint))

    return {"job_id": job_id}


@router.get("/analyze-github-job/{job_id}")
async def get_github_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
