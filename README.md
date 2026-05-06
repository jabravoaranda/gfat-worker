# GFAT Worker

`gfat-worker` is a Dockerized task runner for GFAT operational processing. It exposes a small FastAPI service, queues work through Celery, uses Redis as broker/result backend, and runs scientific processing tasks inside a reproducible Python container.

The current operational focus is ALHAMBRA LIDAR processing with `atmolidarpy` installed as the Python distribution and imported in code as `lidarpy`.

## What It Runs

- FastAPI API: submit tasks and query task status.
- Celery worker: execute Python tasks.
- Celery Beat: run scheduled tasks when enabled.
- Redis: queue broker and result backend.
- Flower: optional operational UI for Celery.

## Repository Map

```text
worker/
  app.py                  Celery application and task registration
  api/                    FastAPI application and request/response models
  tasks/                  Celery task modules
  scheduled/              Celery Beat schedule
  lidar_backend.py        LIDAR import adapter for atmolidarpy/lidarpy
  requirements.txt        Runtime dependencies installed in the Docker image

tests/                    Fast tests run with uv/pytest
scripts/                  Local and deployment helper scripts
docs/                     Architecture, API, and extension guides

docker-compose.yml        Development compose file
docker-compose.test.yml   Local/CI smoke-test compose file
compose.prod.yml          Production compose file for CPD deployment
DEPLOY.md                 Production deployment guide
ROADMAP.md                Current development roadmap
```

## Documentation Website

The repository documentation is a static GitHub Pages site stored in `docs/`.
It follows the same lightweight model as the `lidarpy` documentation site:
plain HTML, CSS, and no build step.

Once Pages is enabled for this repository with source `GitHub Actions`, the
site will be available at:

```text
https://jabravoaranda.github.io/gfat-worker/
```

Preview it locally by opening:

```text
docs/index.html
```

First-time GitHub Pages activation:

1. Open `Settings > Pages` in the GitHub repository.
2. Under `Build and deployment`, set `Source` to `GitHub Actions`.
3. Re-run the `Documentation` workflow or push a change under `docs/`.

The workflow file is `.github/workflows/pages.yml`. GitHub requires the Pages
site to be enabled once at repository level before `actions/deploy-pages` can
publish the artifact.

The documentation workflow follows the same build/deploy split used by
`lidarpy`: the `build` job validates the static site and uploads the Pages
artifact, and the `deploy` job publishes that artifact.

## Main Documentation

- [Overview](docs/index.html)
- [Getting Started](docs/getting-started.html)
- [Architecture](docs/architecture.html)
- [Adding New Tasks](docs/adding-tasks.html)
- [API Usage](docs/api.html)
- [Production Deployment](docs/deployment.html)
- [Roadmap](docs/roadmap.html)

Start with [Adding New Tasks](docs/adding-tasks.html) if you want to implement tasks using another Python package such as `mrrpropy` or `dcrpy`.

## Requirements

For local development:

- Python 3.11
- `uv`
- Docker Desktop or Docker Engine with Docker Compose

For production:

- Linux server
- Docker Engine
- Docker Compose plugin
- mounted RAW and PRODUCTS paths
- non-versioned SCC config file if SCC operations are used

## Fast Local Tests

```bash
uv run pytest -q
```

These tests do not require Docker, Redis, NAS mounts, SCC credentials, or real data.

## Docker Smoke Test

On Windows/PowerShell:

```powershell
.\scripts\smoke_docker.ps1
```

This starts Redis, the worker/API container, and Flower using `docker-compose.test.yml`, queues `tasks.misc.test_sum`, verifies the result, then removes the test stack.

## Development Stack

For the default development compose:

```bash
docker compose up --build
```

The generic API is then available at:

```text
http://localhost:8000/docs
```

The test compose uses ports `18000`, `6380`, and `5555` by default:

```bash
docker compose -f docker-compose.test.yml up --build
```

## Queue A Task

Example:

```json
{
  "task_name": "tasks.misc.test_sum",
  "args": [5, 10],
  "kwargs": {}
}
```

Post it to:

```text
POST /task_queue
```

Then query:

```text
GET /task_queue/{task_id}
```

More examples are in [API Usage](docs/api.html).

## Runtime Dependencies

Runtime dependencies for the worker image live in:

```text
worker/requirements.txt
```

If a new task module needs `mrrpropy`, `dcrpy`, or another package, add the package there, then document any required environment variables or mounted paths.

## CI

GitHub Actions run on push to `main` and on pull requests. The workflow:

- installs dependencies with `uv`
- runs the fast pytest suite
- builds the Docker worker image
- starts Redis/API/worker
- queues a simple Celery task
- verifies the `lidarpy` backend is available
