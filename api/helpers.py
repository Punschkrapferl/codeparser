from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
import math
from pathlib import Path

from pydantic import BaseModel

from api.api_main import BATCH_SIZE
from api.llm_client import call_llm, logger


def _guess_language_from_name(filename: Optional[str]) -> str:
    """Best-effort language guess from file extension."""
    if not filename:
        return "<unknown>"

    ext = Path(filename).suffix.lower()
    if ext == ".py":
        return "python"
    if ext == ".java":
        return "java"
    if ext == ".ts":
        return "typescript"
    if ext == ".js":
        return "javascript"
    if ext == ".go":
        return "go"
    if ext == ".json":
        return "json"
    if ext in {".txt", ".md"}:
        return "text"

    # Typical binary / media will be skipped
    if ext in {".mov", ".mp4", ".avi", ".mkv", ".jpg", ".jpeg", ".png", ".gif"}:
        return "<binary>"

    return "<unknown>"


def _parse_chunks_bytes(raw: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Try to parse the given bytes as:
      1) JSON array of chunk objects, or
      2) JSONL (one object per line).

    If both fail, fall back to treating the whole content as a single
    code/text chunk with path=filename and language guessed from extension.
    """
    text = raw.decode("utf-8", errors="ignore")
    logging.info(
        "parse_chunks: filename=%r, raw=%d bytes, stripped=%d chars",
        filename,
        len(raw),
        len(text.strip()),
    )

    # If it looks like a binary/media file we don't even try to wrap it
    lang_hint = _guess_language_from_name(filename)
    if lang_hint == "<binary>":
        logging.info("parse_chunks: skipping binary/media file %r", filename)
        return []

    if not text.strip():
        return []

    # 1) JSON array
    try:
        arr = json.loads(text)
        if isinstance(arr, list):
            logging.info("parse_chunks: detected JSON array with %d items", len(arr))
            return arr
    except json.JSONDecodeError:
        pass

    # 2) JSONL
    items: List[Dict[str, Any]] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                items.append(obj)
        except json.JSONDecodeError:
            # ignore non-JSON lines
            continue

    if items:
        logging.info("parse_chunks: detected JSONL with %d items", len(items))
        return items

    # 3) Fallback: plain file -> single chunk
    lang = _guess_language_from_name(filename)
    logging.info(
        "parse_chunks: no JSON; fallback single chunk for %r (lang=%r, len=%d)",
        filename,
        lang,
        len(text),
    )
    return [{
        "path": filename or "<uploaded>",
        "language": lang,
        "code": text,
    }]


def _normalize_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Normalize various chunk formats into a uniform schema:
    {path, language, code}.
    """
    parts: List[Dict[str, str]] = []
    for c in chunks:
        path = c.get("path", "<unknown>")
        lang = c.get("language", c.get("Language", "<unknown>"))
        code = c.get("code") or c.get("Code") or ""
        if not isinstance(code, str):
            continue
        if code.strip():
            parts.append({"path": path, "language": lang, "code": code})
    logger.info("normalize_chunks: input=%d, output=%d", len(chunks), len(parts))
    return parts


async def _analyze_parts(
        parts: List[Dict[str, str]],
        system_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Split parts into batches and query the LLM.
    - Each batch becomes one LLM call.
    - Failures in one batch do NOT abort the whole analysis.
    """
    if not parts:
        logger.info("analyze_parts: no parts to analyse.")
        return {"analysis": "", "batches": 0}

    logger.info("analyze_parts: starting analysis for %d parts", len(parts))
    results: List[str] = []
    n_batches = math.ceil(len(parts) / BATCH_SIZE)

    for i in range(n_batches):
        batch = parts[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        logger.info(
            "analyze_parts: batch %d / %d (size=%d)",
            i + 1,
            n_batches,
            len(batch),
            )

        segs: List[str] = []

        if system_hint:
            segs.append(f"[Context]\n{system_hint}\n")

        segs.append(
            "You are a senior backend engineer reviewing multiple source files.\n"
            "Explain everything in clear, simple English so that a junior developer can understand it.\n"
            "\n"
            "For each file, write a markdown section in this format:\n"
            "## <path> (<language>)\n"
            "- Purpose: ...\n"
            "- Key APIs / frameworks: ...\n"
            "- Risks / issues: ...\n"
            "- Suggested improvements: ...\n"
            "\n"
            "After all files, add a final section:\n"
            "## Overall summary\n"
            "- Tech stack: ...\n"
            "- What this service/app does: ...\n"
            "- Biggest risks: ...\n"
            "- Suggested next refactor steps: ...\n"
        )

        for it in batch:
            segs.append(
                f"---\nFile: {it['path']} ({it['language']})\n{it['code']}\n"
            )

        prompt = "\n".join(segs)

        try:
            analysis = await call_llm(prompt)
        except Exception as e:
            logger.exception(
                "analyze_parts: unexpected error in call_llm for batch %d: %s", i, e
            )
            analysis = f"[Batch {i} unexpected error] {e}"

        results.append(f"### Batch {i + 1}/{n_batches}\n{analysis}")

        if i < n_batches - 1:
            await asyncio.sleep(0.25)

    final_text = "\n\n".join(results)
    logger.info(
        "analyze_parts: finished. batches=%d, total analysis length=%d",
        n_batches,
        len(final_text),
    )

    return {
        "analysis": final_text,
        "batches": n_batches,
    }


class AnalyzeIn(BaseModel):
    repo_url: str
    system_hint: Optional[str] = None
