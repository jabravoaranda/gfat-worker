# GFAT - WORKER

A project with Docker Compose with the following containers:

- a **Redis** database used as a broker (tasks queue) and backend (store information about finished jobs)
- **Worker** is a [Celery](https://docs.celeryq.dev/en/stable/index.html) powered task manager connected to redis. Its interface can run scheduled and manage the execution of queued jobs.
- **Flower** is a different container connecting to Redis and displays information about the jobs


## How to use
To start install [Docker](https://docs.docker.com/get-docker/) in your local machine.

Then, it needs to download some images from internet (redis, python), build the containers and run them. It can be achieved with the command

```bash
docker compose up --build
```