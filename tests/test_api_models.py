from __future__ import annotations

from api.models import TaskQueueInput


def test_task_queue_input_accepts_args_and_kwargs():
    body = TaskQueueInput(
        task_name="tasks.misc.test_sum",
        args=[5, 10],
        kwargs={"scale": "unit"},
    )

    assert body.task_name == "tasks.misc.test_sum"
    assert body.args == [5, 10]
    assert body.kwargs == {"scale": "unit"}


def test_task_queue_input_uses_empty_argument_defaults():
    body = TaskQueueInput(task_name="tasks.misc.test_sum")

    assert body.args == []
    assert body.kwargs == {}

