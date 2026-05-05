from typing import cast
from fastapi import FastAPI, HTTPException
from celery.result import AsyncResult

from app import app as celery_app
from api.models import (
    RegisteredTasksResponse,
    TaskQueueDeleteResponse,
    TaskQueueInput,
    TaskQueueResponse,
    TaskQueueDetailsResponse,
)

app = FastAPI()


def serialize_task_result(result):
    if isinstance(result, BaseException):
        return {
            "error_type": result.__class__.__name__,
            "error": str(result),
        }
    return result


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": "API Worker",
        "description": "This is the API Worker service. Go to /docs to see the API documentation.",
    }


@app.get("/registered_tasks")
def get_registered_tasks() -> RegisteredTasksResponse:
    return RegisteredTasksResponse(tasks=celery_app.tasks.keys())


@app.get("/task_queue/{task_id}", tags=["task_management"])
def task_queue_details(task_id: str) -> TaskQueueDetailsResponse:
    task = AsyncResult(task_id, app=celery_app)
    return TaskQueueDetailsResponse(
        id=cast(str, task.task_id),
        state=task.state,
        result=serialize_task_result(task.result),
    )


@app.post("/task_queue", tags=["task_management"])
def task_queue(body: TaskQueueInput) -> TaskQueueResponse:
    if body.task_name not in celery_app.tasks:
        raise HTTPException(
            status_code=400, detail=f"Task '{body.task_name}' is not a registered task"
        )

    try:
        task = celery_app.tasks[body.task_name].apply_async(
            args=body.args, kwargs=body.kwargs
        )
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Error queuing task: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queuing task: {e}")

    return TaskQueueResponse(id=cast(str, task.id))


@app.delete("/task_queue/{task_id}", tags=["task_management"])
def task_queue_delete(task_id: str) -> TaskQueueDeleteResponse:
    # First, check if the task exists using Celery's inspection API
    task = AsyncResult(task_id, app=celery_app)
    task.revoke(signal="SIGKILL", terminate=True)

    return TaskQueueDeleteResponse(id=cast(str, task.id))
