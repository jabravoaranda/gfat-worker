from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

from app import app as celery_app
from scheduled import all_scheduled


def test_schedule_entries_have_required_shape():
    assert all_scheduled

    for name, entry in all_scheduled.items():
        assert name
        assert {"task", "schedule", "args"}.issubset(entry)
        assert isinstance(entry["task"], str)
        assert isinstance(entry["args"], tuple)


def test_schedule_tasks_are_registered():
    registered_tasks = set(celery_app.tasks)

    for entry in all_scheduled.values():
        assert entry["task"] in registered_tasks


def test_schedule_args_match_task_signatures():
    for name, entry in all_scheduled.items():
        task_name = entry["task"]
        module_name, function_name = task_name.rsplit(".", 1)
        task_function = getattr(importlib.import_module(module_name), function_name)
        signature = inspect.signature(task_function)
        positional = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        required = [
            parameter
            for parameter in positional
            if parameter.default is inspect.Parameter.empty
        ]

        assert len(entry["args"]) >= len(required), name
        assert len(entry["args"]) <= len(positional), name


def test_schedule_source_has_no_duplicate_literal_keys():
    source_path = Path(__file__).resolve().parents[1] / "worker" / "scheduled" / "lidar.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    scheduled_dict = next(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "scheduled" for target in node.targets)
    )
    keys = [
        key.value
        for key in scheduled_dict.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    ]

    assert len(keys) == len(set(keys))

