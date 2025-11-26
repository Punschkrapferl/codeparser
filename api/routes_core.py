import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from api.helpers import (
    _parse_chunks_bytes,
    _normalize_chunks,
    _analyze_parts,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory job store for multi-file analyses
FILE_JOBS: Dict[str, Dict[str, Any]] = {}


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/analyze")
async def analyze_code(
        file: UploadFile = File(...),
        system_hint: Optional[str] = Form(None),
):
    """
    OLD one-shot single-file endpoint (kept as-is, but system_hint now comes
    from a normal form field).
    """
    raw = await file.read()
    logger.info("POST /analyze file=%r size=%d", file.filename, len(raw))

    chunks = _parse_chunks_bytes(raw, filename=file.filename)
    parts = _normalize_chunks(chunks)

    out = await _analyze_parts(parts, system_hint)
    languages = sorted(
        {p["language"] for p in parts if p.get("language") not in ("unknown", "<unknown>", None, "")}
    )

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
        system_hint: Optional[str] = Form(None),
):
    """
    OLD synchronous multi-file endpoint (still available).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    all_parts: List[Dict[str, str]] = []
    file_summaries: List[Dict[str, Any]] = []

    for f in files:
        raw = await f.read()
        logger.info("POST /analyze-multi: file=%r size=%d", f.filename, len(raw))

        chunks = _parse_chunks_bytes(raw, filename=f.filename)
        parts = _normalize_chunks(chunks)

        all_parts.extend(parts)
        file_summaries.append(
            {
                "filename": f.filename,
                "num_parts": len(parts),
            }
        )

    out = await _analyze_parts(all_parts, system_hint)
    languages = sorted(
        {p["language"] for p in all_parts if p.get("language") not in ("unknown", "<unknown>", None, "")}
    )

    return {
        "analysis": out.get("analysis", ""),
        "batches": out.get("batches", 0),
        "total_parts": len(all_parts),
        "num_files": len(files),
        "languages": languages,
        "file_summaries": file_summaries,
    }


async def _file_job_worker(
        job_id: str,
        file_blobs: List[Tuple[str, bytes]],
        system_hint: Optional[str],
) -> None:
    """
    Background worker for /analyze-multi-job.
    We keep the uploaded bytes in memory and run the same logic as /analyze-multi.
    """
    FILE_JOBS[job_id]["status"] = "running"
    FILE_JOBS[job_id]["error"] = None

    try:
        all_parts: List[Dict[str, str]] = []
        file_summaries: List[Dict[str, Any]] = []

        for filename, raw in file_blobs:
            logger.info("file-job[%s]: filename=%r size=%d", job_id, filename, len(raw))
            chunks = _parse_chunks_bytes(raw, filename=filename)
            parts = _normalize_chunks(chunks)
            all_parts.extend(parts)
            file_summaries.append(
                {
                    "filename": filename,
                    "num_parts": len(parts),
                }
            )

        out = await _analyze_parts(all_parts, system_hint)
        languages = sorted(
            {p["language"] for p in all_parts if p.get("language") not in ("unknown", "<unknown>", None, "")}
        )

        FILE_JOBS[job_id]["status"] = "done"
        FILE_JOBS[job_id]["result"] = {
            "analysis": out.get("analysis", ""),
            "batches": out.get("batches", 0),
            "total_parts": len(all_parts),
            "num_files": len(file_blobs),
            "languages": languages,
            "file_summaries": file_summaries,
        }

    except Exception as e:  # noqa: BLE001
        logger.exception("file-job[%s] crashed", job_id)
        FILE_JOBS[job_id]["status"] = "error"
        FILE_JOBS[job_id]["error"] = str(e)


@router.post("/analyze-multi-job")
async def start_analyze_multi_job(
        files: List[UploadFile] = File(...),
        system_hint: Optional[str] = Form(None),
):
    """
    NEW job-style endpoint for the file/folder analyser.

    – Accepts the same files as /analyze-multi
    – Returns immediately with a job_id
    – Actual work happens in a background asyncio task
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Read files into memory once; UploadFile objects are not safe to keep.
    file_blobs: List[Tuple[str, bytes]] = []
    for f in files:
        raw = await f.read()
        file_blobs.append((f.filename, raw))

    job_id = str(uuid4())
    FILE_JOBS[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
    }

    # Start background task
    import asyncio

    asyncio.create_task(_file_job_worker(job_id, file_blobs, system_hint))

    return {"job_id": job_id}


@router.get("/analyze-multi-job/{job_id}")
async def get_analyze_multi_job_status(job_id: str):
    job = FILE_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
