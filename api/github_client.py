import subprocess
from pathlib import Path

from fastapi import HTTPException


def clone_or_update(repo_url: str, dest_dir: Path) -> str:
    if not repo_url or len(repo_url) < 5:
        raise HTTPException(status_code=400, detail="repo_url invalid")

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Tests expect folder name = basename of repo URL (without .git)
    repo_name = Path(repo_url.rstrip("/")).stem
    tgt = dest_dir / repo_name

    try:
        # Case 1: Repo already exists -> update
        if (tgt / ".git").exists():
            subprocess.run(
                ["git", "fetch", "--all", "--prune"],
                cwd=tgt,
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["git", "reset", "--hard", "origin/HEAD"],
                cwd=tgt,
                check=True,
                capture_output=True,
                text=True
            )
            return str(tgt)

        # Case 2: Fresh clone
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(tgt)],
            check=True,
            capture_output=True,
            text=True
        )
        return str(tgt)

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="git not found on PATH")

    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or "").strip()
        raise HTTPException(status_code=500, detail=f"git error: {msg}")
