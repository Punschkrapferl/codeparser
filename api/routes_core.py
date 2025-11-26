import logging
from typing import Optional, List, Dict, Any

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Query,
    HTTPException,
)

from api.helpers import (
    _parse_chunks_bytes,
    _normalize_chunks,
    _analyze_parts,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/analyze")
async def analyze_code(
        file: UploadFile = File(...),
        system_hint: Optional[str] = Query(None),
):
    raw = await file.read()
    logger.info("POST /analyze file=%r size=%d", file.filename, len(raw))

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
    languages = sorted({p["language"] for p in all_parts}) if all_parts else []

    return {
        "analysis": out.get("analysis", ""),
        "batches": out.get("batches", 0),
        "total_parts": len(all_parts),
        "num_files": len(files),
        "languages": languages,
        "file_summaries": file_summaries,
    }
