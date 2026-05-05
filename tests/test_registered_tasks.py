from __future__ import annotations

from app import app as celery_app


def test_expected_tasks_are_registered():
    expected_tasks = {
        "tasks.misc.test_sum",
        "tasks.lidar.task_nc_convert",
        "tasks.lidar.task_quicklook",
        "tasks.lidar.task_convert_scc",
        "tasks.lidar.task_send_to_scc",
        "tasks.lidar.task_download_from_scc",
        "tasks.lidar.task_plot_scc",
    }

    assert expected_tasks.issubset(set(celery_app.tasks))

