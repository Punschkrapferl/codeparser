# CodeParser

Full-stack web application for analysing source code repositories (GitHub and local folders) using a FastAPI backend, a Go-based parser and an Angular frontend.  
The project is containerised so that anyone (e.g. recruiters) can run it with a single `docker compose up` command.

---

## Note for reviewers / recruiters

- You can run this project **locally in a few minutes** using Docker; no manual Python / Node setup is required.
- The analysis step uses a **local LLM via Ollama** (free, CPU/GPU dependent).
    - On the **first analysis request**, Ollama may need to **pull and load the model**, which can take **up to ~5 minutes** depending on your machine.
    - Subsequent analyses are significantly faster because the model stays in memory.
- For a quick end‑to‑end demo, you can:
    1. Start the stack with Docker (see [Quick start](#quick-start-docker--recommended)).
    2. Open `http://localhost:4200`.
    3. In the GitHub analyser, paste the URL of one of my public repositories, for example:  
       `https://github.com/<your-github-username>/<another-public-repo>`  
       (any public repo works; using one of my own repos shows how the tool analyses a real project of mine).
    4. Click **Analyze** and wait for the pipeline + LLM summary.  
       If this is the first ever run with the model on your machine, the LLM step may take a few minutes while Ollama warms up.

---

## Table of contents

- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick start (Docker – recommended)](#quick-start-docker--recommended)
    - [Build images](#1-build-images)
    - [Run the stack](#2-run-the-stack)
    - [Use the app](#3-use-the-app)
    - [Stop the stack](#4-stop-the-stack)
- [Local development without Docker](#local-development-without-docker)
    - [Backend (FastAPI)](#backend-fastapi)
    - [Frontend (Angular)](#frontend-angular)
- [How it works (step by step)](#how-it-works-step-by-step)
- [Running tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Architecture

High-level components:

- **Frontend** (`parserUI`)
    - Angular SPA built with Node.
    - Served as static files by an Nginx container.
    - Communicates with the backend over HTTP (`http://localhost:8000` when run via Docker).

- **Backend** (`api`)
    - Python 3.12 + FastAPI.
    - Exposes REST endpoints (e.g. `/health`, `/analyze`, …).
    - Delegates code analysis work to the Go parser.
    - Uses an LLM endpoint (by default a local **Ollama** server) to summarise and interpret analysis results.

- **Parser** (`parser_go`)
    - Go utilities that walk repositories and extract structure/metrics.
    - Called by the Python backend.

- **Repository workspace** (`repos`)
    - On the **host**: `./repos` (git-cloned or analysed code ends up here).
    - In the **container**: mounted at `/app/repos` via Docker volume.
    - This makes results visible both inside the container and on the host.

Everything is orchestrated with **Docker Compose**:

- `backend` service: builds from `Dockerfile.backend`, exposes port `8000`.
- `frontend` service: builds from `parserUI/Dockerfile`, serves Angular app on port `4200`.

---

## Tech stack

- **Backend**
    - Python 3.12
    - FastAPI
    - Uvicorn
    - httpx
    - python-multipart (for file/form uploads)
    - pytest, pytest-asyncio (for tests)

- **Parser**
    - Go (installed inside the backend image)

- **Frontend**
    - Angular
    - TypeScript
    - Node 22 (build)
    - Nginx (runtime)

- **LLM / analysis**
    - Local LLM served via **Ollama** (free; first model load can take several minutes)

- **Containerisation**
    - Docker
    - Docker Compose v2 (`docker compose`)

---

## Project structure

```text
codeparser/
├─ api/                  # FastAPI backend (Python)
│  ├─ main.py            # FastAPI app entry
│  ├─ routes_core.py     # Core API routes (/analyze, ...)
│  ├─ tests/             # Backend tests (pytest)
│  └─ requirements.txt   # Backend Python dependencies (incl. pytest, pytest-asyncio)
├─ parser_go/            # Go parsing logic called from backend
├─ parserUI/             # Angular frontend
│  ├─ src/               # Angular source (components, services, ...)
│  ├─ Dockerfile         # Frontend Dockerfile (multi-stage: Node + Nginx)
│  └─ nginx.conf         # Nginx config for SPA routing
├─ repos/                # Workspace where cloned / analysed repos are stored
├─ Dockerfile.backend    # Backend Dockerfile
├─ docker-compose.yml    # Compose definition (frontend + backend services)
├─ pytest.ini            # Pytest config for backend tests
└─ __init__.py           # Marks root package
```

---

## Prerequisites

To run with Docker (recommended):

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
- Docker Compose v2 (part of modern Docker – command: `docker compose`)

To use LLM-based analysis (optional but recommended):

- [Ollama](https://ollama.com/) installed and running locally, with a suitable model pulled (for example, `llama3` or similar).
    - The backend expects an Ollama endpoint reachable from inside the container (e.g. via `http://host.docker.internal:11434` or as configured in environment variables).
    - First model load can take **up to ~5 minutes**.

To develop without Docker (optional):

- Python 3.12 and `pip`
- Node.js (≥ 18) + npm
- Go (for running parser locally, if desired)

---

## Quick start (Docker – recommended)

All commands below are run from the project root folder, e.g.:

```bash
cd codeparser
```

### 1. Build images

The first time (or after changing Dockerfiles / requirements):

```bash
docker compose build
```

This performs:

- Build **backend image** from `Dockerfile.backend`.
- Build **frontend image** from `parserUI/Dockerfile`.
- Cache Python and Node dependencies for faster rebuilds.

You can always rebuild just one service, for example:

```bash
docker compose build backend
docker compose build frontend
```

### 2. Run the stack

Start both services:

```bash
docker compose up
```

Expected output:

- A `codeparser-backend` container with FastAPI starting under Uvicorn.
- A `codeparser-frontend` container with Nginx serving the Angular build.
- Log lines similar to:
    - `Uvicorn running on http://0.0.0.0:8000`
    - `nginx/1.28.0` startup messages

To run detached (background):

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

You should see:

- `codeparser-backend` – `running`
- `codeparser-frontend` – `running`

> **Important:** On the **first end‑to‑end analysis**, the LLM step (via Ollama) may take **up to ~5 minutes** while the model is pulled and loaded. This is expected for a free local setup. Later requests are much faster.

### 3. Use the app

Open in a browser:

- **Frontend UI**  
  `http://localhost:4200`

- **Backend API docs (Swagger / OpenAPI)**  
  `http://localhost:8000/docs`

Typical workflow in the UI (may vary slightly depending on the current version):

1. **GitHub repository analyser**
    - Enter a GitHub repository URL (for example, one of my public repos from my GitHub profile).
    - Click the **Analyze** button.
    - The frontend calls the backend, which:
        - clones the repository into `/app/repos` (visible as `./repos` on the host),
        - runs the Go parser and aggregates results,
        - optionally calls the LLM via Ollama to summarise findings,
        - returns structured analysis to the UI.

2. **Folder / file analyser**
    - Upload local files or a zipped project.
    - The backend stores the upload under `/app/repos` and runs the parser.
    - Results are displayed in the UI.

Both flows can show status updates / progress and then render the analysis (e.g. file tree, metrics, summaries, etc.).

### 4. Stop the stack

In the terminal running `docker compose up`:

- Press `Ctrl + C`.

Then clean up containers and the network:

```bash
docker compose down
```

The `./repos` folder on the host is **not** removed; it keeps cloned projects for inspection.

---

## Local development without Docker

Running without containers can be useful during active development.

### Backend (FastAPI)

From the project root:

1. Create and activate a virtual environment (optional but recommended).

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   # .venv\Scripts\activate   # Windows PowerShell
   ```

2. Install dependencies.

   ```bash
   pip install -r api/requirements.txt
   ```

3. Run the backend with reload.

   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Verify backend.

   Open `http://localhost:8000/docs` in a browser.

### Frontend (Angular)

From the `parserUI/` directory:

1. Install Node dependencies:

   ```bash
   cd parserUI
   npm install
   ```

2. Start the dev server (adjust script name if needed):

   ```bash
   npm run start        # or: ng serve
   ```

3. Open the Angular dev server:

    - `http://localhost:4200`

Ensure the frontend’s API base URL points to `http://localhost:8000` when running backend locally.

---

## How it works (step by step)

This section explains “what to run and when” from a developer’s point of view.

### First time setup

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-username>/codeparser.git
   cd codeparser
   ```

2. Build Docker images (once, or whenever dependencies change):

   ```bash
   docker compose build
   ```

3. Start the stack:

   ```bash
   docker compose up
   ```

4. Use the app via the browser (`:4200`) and the API docs (`:8000/docs`).

### Normal development cycle

When you change **only code** (not requirements):

1. Start services (will reuse existing images):

   ```bash
   docker compose up
   ```

2. Edit code in your editor/IDE.
3. When you want a clean restart, stop with `Ctrl + C` and start again.

When you change **dependencies** (`api/requirements.txt` or `parserUI/package*.json`):

1. Rebuild the affected image:

   ```bash
   docker compose build backend   # for Python dependency changes
   docker compose build frontend  # for Angular/Node dependency changes
   ```

2. Restart:

   ```bash
   docker compose up
   ```

### What each file is responsible for

- `docker-compose.yml`
    - Defines two services: `backend` and `frontend`.
    - Maps backend port `8000` and frontend port `4200` to the host.
    - Mounts `./repos` on the host into `/app/repos` in the backend container.

- `Dockerfile.backend`
    - Base: `python:3.12-slim`.
    - Installs system tools (`git`, `golang`, `build-essential`).
    - Installs Python dependencies from `api/requirements.txt`.
    - Copies backend and parser code.
    - Starts `uvicorn api.main:app` on port `8000`.

- `parserUI/Dockerfile`
    - Stage 1: Node image builds Angular app (`npm ci` + `npm run build`).
    - Stage 2: Nginx image serves the built Angular static files.
    - `nginx.conf` ensures SPA routing (all routes fallback to `index.html`).

- `parserUI/nginx.conf`
    - Minimal Nginx config for a single-page app:
        - Serve static files from `/usr/share/nginx/html`.
        - `try_files` rule to send unknown paths to `index.html`.

---

## Running tests

### Backend tests (pytest)

Inside Docker:

```bash
docker compose run --rm backend pytest
```

This:

- Starts a temporary `backend` container.
- Runs `pytest` inside it.
- Cleans up the container afterwards.

Locally (without Docker):

```bash
cd codeparser
source .venv/bin/activate     # if using a venv
pytest
```

### Frontend tests (Angular)

From `parserUI/`:

```bash
cd parserUI
npm test
```

(Assumes the standard Angular test setup is present.)

---

## Troubleshooting

### “Cannot connect to the Docker daemon”

Error:

```text
Cannot connect to the Docker daemon at unix:///.../docker.sock. Is the docker daemon running?
```

- Make sure Docker Desktop is running.
- On Linux, ensure your user is in the `docker` group or use `sudo`.

### Backend container exits with `python-multipart` error

Error:

```text
RuntimeError: Form data requires "python-multipart" to be installed.
```

Fix (already applied in this project):

- Ensure `python-multipart` is present in `api/requirements.txt`.
- Rebuild backend:

  ```bash
  docker compose build backend
  docker compose up
  ```

### Async tests fail with “async def functions are not natively supported”

- Ensure `pytest-asyncio` is present in `api/requirements.txt`.
- Optionally register the marker in `pytest.ini`:

  ```ini
  [pytest]
  markers =
      asyncio: mark test as asyncio
  ```

- Rebuild and rerun tests:

  ```bash
  docker compose build backend
  docker compose run --rm backend pytest
  ```

### Ports already in use

If `8000` or `4200` are in use:

- Stop other services using those ports.
- Or change port mappings in `docker-compose.yml`, for example:

  ```yaml
  ports:
    - "8080:8000"  # host:container
  ```

Then visit `http://localhost:8080` instead of `8000`.

---

## License

MIT License

Copyright (c) 2025 Punschkrapferl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
