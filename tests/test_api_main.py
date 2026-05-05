from __future__ import annotations

from api.main import serialize_task_result


def test_serialize_task_result_formats_exceptions():
    result = serialize_task_result(ValueError("bad task input"))

    assert result == {
        "error_type": "ValueError",
        "error": "bad task input",
    }


def test_serialize_task_result_keeps_normal_results():
    result = {"files": ["20230830gra0315.nc"]}

    assert serialize_task_result(result) == result
