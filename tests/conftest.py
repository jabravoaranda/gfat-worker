from __future__ import annotations

import importlib.util
import sys
import types
from enum import Enum
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKER_DIR = ROOT / "worker"
if str(WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(WORKER_DIR))


def _install_module(name: str, module: types.ModuleType) -> types.ModuleType:
    sys.modules.setdefault(name, module)
    return sys.modules[name]


def _ensure_celery_stub() -> None:
    if importlib.util.find_spec("celery") is not None:
        return

    shared_tasks: dict[str, Any] = {}

    def shared_task(func):
        task_name = f"{func.__module__}.{func.__name__}"
        func.name = task_name
        shared_tasks[task_name] = func
        return func

    class _Conf:
        pass

    class Celery:
        def __init__(self, *args, **kwargs):
            self.tasks: dict[str, Any] = {}
            self.conf = _Conf()

        def autodiscover_tasks(self, packages, force=False):
            import importlib

            for package in packages:
                importlib.import_module(package)
            self.tasks.update(shared_tasks)

    class AsyncResult:
        def __init__(self, task_id, app=None):
            self.task_id = task_id
            self.id = task_id
            self.state = "PENDING"
            self.result = None

        def revoke(self, signal=None, terminate=False):
            return None

    def crontab(*args, **kwargs):
        return {"args": args, "kwargs": kwargs}

    celery = types.ModuleType("celery")
    celery.Celery = Celery
    celery.shared_task = shared_task

    celery_result = types.ModuleType("celery.result")
    celery_result.AsyncResult = AsyncResult

    celery_schedules = types.ModuleType("celery.schedules")
    celery_schedules.crontab = crontab

    _install_module("celery", celery)
    _install_module("celery.result", celery_result)
    _install_module("celery.schedules", celery_schedules)


def _ensure_fastapi_stub() -> None:
    if importlib.util.find_spec("fastapi") is not None:
        return

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    class FastAPI:
        def get(self, *args, **kwargs):
            return lambda func: func

        def post(self, *args, **kwargs):
            return lambda func: func

        def delete(self, *args, **kwargs):
            return lambda func: func

    fastapi = types.ModuleType("fastapi")
    fastapi.FastAPI = FastAPI
    fastapi.HTTPException = HTTPException
    _install_module("fastapi", fastapi)


def _ensure_pydantic_stub() -> None:
    if importlib.util.find_spec("pydantic") is not None:
        return

    missing = object()

    class FieldInfo:
        def __init__(self, default=missing, default_factory=None, **kwargs):
            self.default = default
            self.default_factory = default_factory

    def Field(default=missing, default_factory=None, **kwargs):
        return FieldInfo(default=default, default_factory=default_factory, **kwargs)

    class BaseModel:
        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                class_value = getattr(self.__class__, name, missing)
                if name in data:
                    value = data[name]
                elif isinstance(class_value, FieldInfo):
                    if class_value.default_factory is not None:
                        value = class_value.default_factory()
                    elif class_value.default is not missing:
                        value = class_value.default
                    else:
                        raise TypeError(f"Missing required field: {name}")
                elif class_value is not missing:
                    value = class_value
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)

    pydantic = types.ModuleType("pydantic")
    pydantic.BaseModel = BaseModel
    pydantic.Field = Field
    _install_module("pydantic", pydantic)


def _ensure_lidarpy_stub() -> None:
    if importlib.util.find_spec("lidarpy") is not None:
        return

    class LidarName(str, Enum):
        alh = "alhambra"
        mhc = "mulhacen"
        gnl = "generalife"

    class MeasurementType(str, Enum):
        RS = "RS"
        DC = "DC"
        DP = "DP"

    class Measurement:
        pass

    def to_measurements(*args, **kwargs):
        return []

    def quicklook_from_file(*args, **kwargs):
        return None

    def find_nearest_filepath(*args, **kwargs):
        return Path("dummy.py")

    def read_yaml(*args, **kwargs):
        return {}

    def licel_to_datetime(*args, **kwargs):
        from datetime import datetime

        return datetime(2024, 1, 1)

    lidar_info = {
        "metadata": {
            "name2nick": {"alhambra": "alh"},
            "nick2name": {"alh": "alhambra"},
        }
    }

    modules = {
        "lidarpy": types.ModuleType("lidarpy"),
        "lidarpy.general_utils": types.ModuleType("lidarpy.general_utils"),
        "lidarpy.general_utils.io": types.ModuleType("lidarpy.general_utils.io"),
        "lidarpy.nc_convert": types.ModuleType("lidarpy.nc_convert"),
        "lidarpy.nc_convert.measurement": types.ModuleType(
            "lidarpy.nc_convert.measurement"
        ),
        "lidarpy.plot": types.ModuleType("lidarpy.plot"),
        "lidarpy.plot.quicklook": types.ModuleType("lidarpy.plot.quicklook"),
        "lidarpy.utils": types.ModuleType("lidarpy.utils"),
        "lidarpy.utils.types": types.ModuleType("lidarpy.utils.types"),
        "lidarpy.utils.utils": types.ModuleType("lidarpy.utils.utils"),
    }

    modules["lidarpy.general_utils.io"].find_nearest_filepath = find_nearest_filepath
    modules["lidarpy.general_utils.io"].read_yaml = read_yaml
    modules["lidarpy.nc_convert.measurement"].Measurement = Measurement
    modules["lidarpy.nc_convert.measurement"].to_measurements = to_measurements
    modules["lidarpy.plot.quicklook"].BoundsType = object
    modules["lidarpy.plot.quicklook"].quicklook_from_file = quicklook_from_file
    modules["lidarpy.utils.types"].LidarName = LidarName
    modules["lidarpy.utils.types"].MeasurementType = MeasurementType
    modules["lidarpy.utils.utils"].LIDAR_INFO = lidar_info
    modules["lidarpy.utils.utils"].licel_to_datetime = licel_to_datetime

    for name, module in modules.items():
        _install_module(name, module)


def _ensure_gfatpy_scc_stub() -> None:
    if importlib.util.find_spec("gfatpy") is not None:
        return

    class SCC:
        def __init__(self, *args, **kwargs):
            pass

    def check_measurement_id_in_scc(*args, **kwargs):
        return False, None

    class SCC_zipfile:
        def __init__(self, *args, **kwargs):
            pass

        def plot(self, *args, **kwargs):
            return []

    class _Licel2Scc:
        @staticmethod
        def create_custom_class(*args, **kwargs):
            return object

    class _Licel2SccDepol(_Licel2Scc):
        @staticmethod
        def create_custom_dark_class(*args, **kwargs):
            return object

    modules = {
        "gfatpy": types.ModuleType("gfatpy"),
        "gfatpy.lidar": types.ModuleType("gfatpy.lidar"),
        "gfatpy.lidar.scc": types.ModuleType("gfatpy.lidar.scc"),
        "gfatpy.lidar.scc.plot": types.ModuleType("gfatpy.lidar.scc.plot"),
        "gfatpy.lidar.scc.plot.scc_zip": types.ModuleType(
            "gfatpy.lidar.scc.plot.scc_zip"
        ),
        "gfatpy.lidar.scc.transfer": types.ModuleType("gfatpy.lidar.scc.transfer"),
        "gfatpy.lidar.scc.licel2scc": types.ModuleType(
            "gfatpy.lidar.scc.licel2scc"
        ),
    }

    modules["gfatpy"].GFATPY_DIR = ROOT / "fake-gfatpy"
    modules["gfatpy.lidar.scc"].scc_access = types.SimpleNamespace(SCC=SCC)
    modules["gfatpy.lidar.scc.plot.scc_zip"].SCC_zipfile = SCC_zipfile
    modules["gfatpy.lidar.scc.transfer"].check_measurement_id_in_scc = (
        check_measurement_id_in_scc
    )
    modules["gfatpy.lidar.scc.licel2scc"].licel2scc = _Licel2Scc
    modules["gfatpy.lidar.scc.licel2scc"].licel2scc_depol = _Licel2SccDepol

    for name, module in modules.items():
        _install_module(name, module)


_ensure_celery_stub()
_ensure_fastapi_stub()
_ensure_pydantic_stub()
_ensure_lidarpy_stub()
_ensure_gfatpy_scc_stub()

