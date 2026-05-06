from __future__ import annotations

from datetime import date
from pathlib import Path

from tasks.lidar import cleanup_measurement_tmp, measurement_to_nc


def test_measurement_to_nc_uses_legacy_target_date_signature():
    class LegacyMeasurement:
        def __init__(self):
            self.kwargs = None

        def to_nc(self, target_date=None, output_dir=None):
            self.kwargs = {"target_date": target_date, "output_dir": output_dir}

    measurement = LegacyMeasurement()

    measurement_to_nc(measurement, date(2023, 8, 30), Path("/products"))

    assert measurement.kwargs == {
        "target_date": date(2023, 8, 30),
        "output_dir": Path("/products"),
    }


def test_measurement_to_nc_uses_current_lidarpy_signature():
    class CurrentMeasurement:
        def __init__(self):
            self.kwargs = None

        def to_nc(self, output_dir=None, by_dates=False):
            self.kwargs = {"output_dir": output_dir, "by_dates": by_dates}

    measurement = CurrentMeasurement()

    measurement_to_nc(measurement, date(2023, 8, 30), Path("/products"))

    assert measurement.kwargs == {
        "output_dir": Path("/products"),
        "by_dates": True,
    }


def test_cleanup_measurement_tmp_does_not_require_unzipped_path():
    class Measurement:
        path = Path("RS_20230830_0315.zip")

        def __init__(self):
            self.removed = False

        def remove_tmp_unzipped_dir(self):
            self.removed = True

    measurement = Measurement()

    cleanup_measurement_tmp(measurement)

    assert measurement.removed is True


def test_cleanup_measurement_tmp_accepts_measurements_without_cleanup_method():
    class Measurement:
        pass

    cleanup_measurement_tmp(Measurement())
