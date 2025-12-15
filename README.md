# CodeParser
Full-stack web application for analysing source code repositories (GitHub and local folders) using a FastAPI backend, a Go-
The project is containerised so that anyone (e.g. recruiters) can run it with a single:
```bash
  docker compose -f docker-compose.demo.yml up
```
---
## Quick start (TL;DR for reviewers)
Install **Docker** and **Ollama**. Ensure both are running.
1. **Clone the repo & start the demo stack**
```bash

git clone https://github.com/Punschkrapferl/codeparser.git
cd codeparser
docker compose -f docker-compose.demo.yml pull
docker compose -f docker-compose.demo.yml up
```
2. **Open the frontend**
- Frontend UI: `http://localhost:4200`
3. **Run a demo analysis**
   In the GitHub analyser view, paste:
```text
https://github.com/Punschkrapferl/MovieGold
```
Click **Analyze** and wait for the pipeline + LLM summary.
Depending on your machine and the LLM model, this can take **up to a few minutes per run**.
- If Ollama is **not** running, the core static analysis still works.
- In that case, the LLM summary section will be missing or replaced by an “LLM unavailable” message.
4. **Stop the stack**
   In the terminal running Compose, press `Ctrl + C`, then:
```bash
  docker compose -f docker-compose.demo.yml down
```
---
## Note for reviewers / recruiters
- You can run this project **locally in a few minutes** using Docker; no manual Python / Node setup is required.
- This repository includes two Docker Compose files:
- `docker-compose.demo.yml`: pulls prebuilt images from Docker Hub (**recommended for reviewers**).
- `docker-compose.dev.yml`: builds images locally from source (**for development**).
- The demo setup pulls these pinned images from Docker Hub:
- Backend image: `punschkrapferl23/codeparser-backend:v1.0.0`
- Frontend image: `punschkrapferl23/codeparser-frontend:v1.0.0`
- The analysis pipeline:
- clones a target GitHub repository,
- parses it with a Go-based static analyser,
- then calls a **local LLM via Ollama** (free, CPU/GPU dependent) to generate higher-level summaries.
- The LLM step always runs the repository through the model in **batches with limited chunk sizes**.
  With a local Ollama model, this means:
- Each full analysis is relatively heavy and can easily take **up to ~5 minutes** on a typical laptop.
- This is not just a one-time startup cost; every analysis will process all batches again.
- To keep the overall waiting time reasonable, please use a **small repository** for your first run.
- Recommended demo repo (one of my own projects):
```text
https://github.com/Punschkrapferl/MovieGold
```
This repository is intentionally small, so most of the waiting time comes from the LLM step rather than git cloning.
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
- **Demo (recommended)**: `docker-compose.demo.yml`
- `backend` service: pulls `punschkrapferl23/codeparser-backend:v1.0.0`
- `frontend` service: pulls `punschkrapferl23/codeparser-frontend:v1.0.0`
- **Development**: `docker-compose.dev.yml`
- Builds the backend from `Dockerfile.backend`
- Builds the frontend from `parserUI/Dockerfile`
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
- Local LLM served via **Ollama** (each run processes the repository in batches)
- **Containerisation**
- Docker
- Docker Compose v2 (`docker compose`)
---
## Project structure
```text
codeparser/
■■ api/ # FastAPI backend (Python)
■ ■■ main.py # FastAPI app entry
■ ■■ routes_core.py # Core API routes (/analyze, ...)
■ ■■ tests/ # Backend tests (pytest)
■ ■■ requirements.txt # Backend Python dependencies (incl. pytest, pytest-asyncio)
■■ parser_go/ # Go parsing logic called from backend
■■ parserUI/ # Angular frontend
■ ■■ src/ # Angular source (components, services, ...)
■ ■■ Dockerfile # Frontend Dockerfile (multi-stage: Node + Nginx)
■ ■■ nginx.conf # Nginx config for SPA routing
■■ repos/ # Workspace where cloned / analysed repos are stored
■■ Dockerfile.backend # Backend Dockerfile
■■ docker-compose.demo.yml # Demo Compose (prebuilt images for reviewers)
■■ docker-compose.dev.yml # Dev Compose (builds images locally)
■■ pytest.ini # Pytest config for backend tests
■■ __init__.py # Marks root package
```
---
## Prerequisites
To run with Docker (recommended):
- Docker Desktop or Docker Engine
- Docker Compose v2 (part of modern Docker – command: `docker compose`)
  To use LLM-based analysis (optional but recommended):
- [Ollama](https://ollama.com/) installed and running locally, with a suitable model pulled (for example, `mistral:latest` or `llam
- The backend expects an Ollama endpoint reachable from inside the container, configured via environment variables in `d
- `OLLAMA_HOST` (e.g. `http://host.docker.internal:11434`)
- `MODEL_NAME` (e.g. `mistral:latest`)
- First model pull + load can take **several minutes**.
- Subsequent runs re-use the loaded model but still need time for all batches to be processed.
  To develop without Docker (optional):
- Python 3.12 and `pip`
- Node.js (≥ 18) + npm
- Go (for running the parser locally, if desired)
---
## Quick start (Docker – detailed)
All commands below are run from the project root folder, e.g.:
```bash
  cd codeparser
```
### 1. Run the stack (using prebuilt images)
The repo’s `docker-compose.demo.yml` references prebuilt Docker Hub images, so you **do not need to build** anything fo
```bash
  docker compose -f docker-compose.demo.yml up
```
Docker will:
- Pull `punschkrapferl23/codeparser-backend:v1.0.0` and `punschkrapferl23/codeparser-frontend:v1.0.0` if they are not pres
- Start both containers and connect them to a shared network.
- Mount `./repos` from the host into `/app/repos` inside the backend container.
  To run detached (background):
```bash
  docker compose -f docker-compose.demo.yml up -d
```
Check running containers:
```bash
  docker compose -f docker-compose.demo.yml ps
```
You should see:
- `codeparser-backend` – `running`
- `codeparser-frontend` – `running`
> **Important:** On a full analysis with the LLM enabled, the Ollama step can take **up to ~5 minutes** for a small repo on a
### 2. Use the app
Open in a browser:
- **Frontend UI**: `http://localhost:4200`
- **Backend API docs (Swagger / OpenAPI)**: `http://localhost:8000/docs`
  Typical workflow in the UI (may vary slightly depending on the current version):
1. **GitHub repository analyser**
- Enter a GitHub repository URL (for example, the recommended demo repo:
  `https://github.com/Punschkrapferl/MovieGold`)
- Click the **Analyze** button.
- The frontend calls the backend, which:
- clones the repository into `/app/repos` (visible as `./repos` on the host),
- runs the Go parser and aggregates results,
- calls the LLM via Ollama to summarise findings (if Ollama is running),
- returns structured analysis to the UI.
2. **Folder / file analyser**
- Upload local files or a zipped project.
- The backend stores the upload under `/app/repos` and runs the parser.
- Results are displayed in the UI.
  Both flows can show status updates / progress and then render the analysis (e.g. file tree, metrics, summaries, etc.).
### 3. Stop the stack
In the terminal running `docker compose -f docker-compose.demo.yml up`:
- Press `Ctrl + C`.
  Then clean up containers and the network:
```bash
  docker compose -f docker-compose.demo.yml down
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
  source .venv/bin/activate # macOS / Linux
  # .venv\Scripts\activate # Windows PowerShell
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

npm run start ```
# or: ng serve
3. Open the Angular dev server:
- `http://localhost:4200`
Ensure the frontend’s API base URL points to `http://localhost:8000` when running the backend locally.
---
## How it works (developer view)
### First time setup
1. Clone the repository:
```bash
git clone https://github.com/Punschkrapferl/codeparser.git
cd codeparser
```
2. Start the stack (using prebuilt images):
```bash
  docker compose -f docker-compose.demo.yml up
```
3. Use the app via the browser (`:4200`) and the API docs (`:8000/docs`).
### Normal development cycle
When you change **only code** (not dependencies):
- For reviewers using prebuilt images, no rebuild step is required; they just run:
```bash
  docker compose -f docker-compose.demo.yml up
```
- For your own development:
- You can build new images locally (see below) and retag/push them to Docker Hub, then `docker compose -f docker-comp
When you change **dependencies** (`api/requirements.txt` or `parserUI/package*.json`) and want new images:
1. Build local images manually, e.g.:
```bash
    # Backend
    docker build -f Dockerfile.backend -t punschkrapferl23/codeparser-backend:v1.0.0 .
    # Frontend
    docker build -f parserUI/Dockerfile -t punschkrapferl23/codeparser-frontend:v1.0.0 parserUI
```
2. Push them (optional, for sharing with others):
```bash
  docker push punschkrapferl23/codeparser-backend:v1.0.0
  docker push punschkrapferl23/codeparser-frontend:v1.0.0
```
3. Restart:
```bash
  docker compose -f docker-compose.demo.yml up
```
Alternatively, for fully local dev builds you can use `docker-compose.dev.yml`:
```bash
  docker compose -f docker-compose.dev.yml up --build
```
---
## What each file is responsible for
- `docker-compose.demo.yml`
- Defines two services: `backend` and `frontend`.
- Uses prebuilt images from Docker Hub.
- Maps backend port `8000` and frontend port `4200` to the host.
- Mounts `./repos` on the host into `/app/repos` in the backend container.
- Passes `OLLAMA_HOST` and `MODEL_NAME` to the backend.
- `docker-compose.dev.yml`
- Dev variant that builds backend & frontend images locally from source.
- `Dockerfile.backend`
- Base image: `python:3.12-slim`.
- Installs system tools (`git`, `golang`, `build-essential`).
- Installs Python dependencies from `api/requirements.txt`.
- Copies backend and parser code.
- Starts `uvicorn api.main:app` on port `8000`.
- `parserUI/Dockerfile`
- Stage 1: Node image builds Angular app (`npm ci` + `npm run build`).
- Stage 2: Nginx image serves the built Angular static files.
- Uses `nginx.conf` to ensure SPA routing (all routes fall back to `index.html`).
- `parserUI/nginx.conf`
- Minimal Nginx config for a single-page app:
- Serve static files from `/usr/share/nginx/html`.
- `try_files` rule to send unknown paths to `index.html`.
---
## Running tests
### Backend tests (pytest)
Inside Docker (using the prebuilt backend image):
```bash
  docker compose -f docker-compose.demo.yml run --rm backend pytest
```
This:
- Starts a temporary `backend` container from the prebuilt image.
- Runs `pytest` inside it.
- Cleans up the container afterwards.
  Locally (without Docker):
```bash
  cd codeparser
  source .venv/bin/activate pytest
```
# if using a venv
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
```
Cannot connect to the Docker daemon at unix:///.../docker.sock. Is the docker daemon running?
```

- Make sure Docker Desktop is running.
- On Linux, ensure your user is in the `docker` group or use `sudo`.

### Backend container exits with `python-multipart` error (local builds)

Error (for local image builds):
```
RuntimeError: Form data requires "python-multipart" to be installed.
```
Fix (already applied in this project):
- Ensure `python-multipart` is present in `api/requirements.txt`.
- Rebuild backend image locally:
```bash
  docker build -f Dockerfile.backend -t punschkrapferl23/codeparser-backend:v1.0.0 .
```

### Async tests fail with “async def functions are not natively supported”
- Ensure `pytest-asyncio` is present in `api/requirements.txt`.
- Optionally register the marker in `pytest.ini`:
```ini
[pytest]
markers =
asyncio: mark test as asyncio
```
- Rebuild and rerun tests in Docker if needed:
```bash
  docker build -f Dockerfile.backend -t punschkrapferl23/codeparser-backend:v1.0.0 .
  docker compose -f docker-compose.demo.yml run --rm backend pytest
```
### Ports already in use
If `8000` or `4200` are in use:
- Stop other services using those ports.
- Or change port mappings in `docker-compose.demo.yml`, for example:
```yaml
ports:
- "8080:8000" # host:container
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