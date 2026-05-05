from __future__ import annotations

from api.models import TaskQueueInput
from api.models import TaskQueueDetailsResponse


def test_task_queue_input_accepts_args_and_kwargs():
    body = TaskQueueInput(
        task_name="tasks.misc.test_sum",
        args=[5, 10, {"nested": True}],
        kwargs={"scale": "unit", "scc_id": 781},
    )

    assert body.task_name == "tasks.misc.test_sum"
    assert body.args == [5, 10, {"nested": True}]
    assert body.kwargs == {"scale": "unit", "scc_id": 781}
    assert isinstance(body.args[0], int)


def test_task_queue_input_uses_empty_argument_defaults():
    body = TaskQueueInput(task_name="tasks.misc.test_sum")

    assert body.args == []
    assert body.kwargs == {}


def test_task_queue_details_accepts_structured_results():
    response = TaskQueueDetailsResponse(
        id="task-id",
        state="SUCCESS",
        result={"backend": "lidarpy", "has_alhambra": True},
    )

    assert response.result["backend"] == "lidarpy"
