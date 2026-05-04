from pydantic import BaseModel, Field


class RegisteredTasksResponse(BaseModel):
    tasks: list[str] = Field(
        title="Registered tasks", description="The names of the registered tasks"
    )


class TaskQueueInput(BaseModel):
    task_name: str = Field(
        title="Task name",
        description="The name of the task to queue",
        examples=["tasks.misc.test_sum"],
    )
    args: list[float | str] = Field(
        default_factory=list,
        title="Task arguments",
        description="The arguments to pass to the task",
        examples=[[5, 10]],
    )
    kwargs: dict[str, float | str] = Field(
        default_factory=dict,
        title="Task keyword arguments",
        description="The keyword arguments to pass to the task",
        examples=[{}],
    )


class TaskQueueResponse(BaseModel):
    id: str = Field(title="Task ID", description="The ID of the queued task")


class TaskQueueDetailsResponse(BaseModel):
    id: str = Field(title="Task ID", description="The ID of the task")
    state: str = Field(title="Task state", description="The state of the task")
    result: float | str | None = Field(
        title="Task result", description="The result of the task"
    )


class TaskQueueDeleteResponse(BaseModel):
    id: str = Field(title="Task ID", description="The ID of the task")
