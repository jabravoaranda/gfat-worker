# GFAT - WORKER

A project with Docker Compose with the following containers:

- a **Redis** database used as a broker (tasks queue) and backend (store information about finished jobs)
- **Worker** is a [Celery](https://docs.celeryq.dev/en/stable/index.html) powered task manager connected to Redis. Its interface can run scheduled and manage the execution of queued jobs.
- **Flower** is a different container connecting to Redis and displays information about the jobs.

## How to use

Install [Docker](https://docs.docker.com/get-docker/) in your local machine.

Then build and run the services with:

```bash
docker compose up --build
```

## Tests

Run the fast no-Docker test suite with `uv`:

```bash
uv run pytest -q
```

These tests validate imports, API models, task registration, schedule structure,
date handling, and interval parsing without starting Redis, Celery workers,
Docker, NAS mounts, or SCC connections.

Run the Docker smoke test with:

```powershell
.\scripts\smoke_docker.ps1
```

This starts a test-only Redis and worker/API stack, queues
`tasks.misc.test_sum`, verifies the result, and then removes the test
containers. It does not mount NAS paths or contact SCC.
