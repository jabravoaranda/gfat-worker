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
