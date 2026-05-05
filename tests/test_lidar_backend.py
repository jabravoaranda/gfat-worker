from __future__ import annotations

import lidar_backend


def test_lidar_backend_exposes_required_symbols():
    assert lidar_backend.LIDAR_BACKEND in {"lidarpy", "gfatpy"}

    for symbol in [
        "LIDAR_INFO",
        "LidarName",
        "to_measurements",
        "quicklook_from_file",
    ]:
        assert hasattr(lidar_backend, symbol)

