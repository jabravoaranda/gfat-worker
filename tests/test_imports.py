from __future__ import annotations

import importlib


def test_worker_modules_import_without_external_services():
    for module_name in ["app", "api.main", "tasks.misc", "tasks.lidar"]:
        importlib.import_module(module_name)

