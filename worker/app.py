import os

from celery import Celery

from scheduled import all_scheduled


app = Celery(
    "app",
    broker=os.environ.get("BROKER_URL"),
    backend=os.environ.get("BROKER_URL")
)

app.autodiscover_tasks([
    "tasks.lidar",
    "tasks.misc",
    # "tasks.radar" Ej. de añadir
    ],
    force=True
)

app.conf.timezone = "Europe/Madrid" # type: ignore
app.conf.beat_schedule = all_scheduled
app.conf.broker_connection_retry_on_startup = True