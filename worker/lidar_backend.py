try:
    from lidarpy.general_utils.io import find_nearest_filepath, read_yaml
    from lidarpy.nc_convert.measurement import Measurement
    try:
        from lidarpy.nc_convert.measurement import to_measurements
    except ImportError:
        from lidarpy.utils.types import MeasurementType

        def to_measurements(lidar_name: str, glob):
            measurements = []
            for path in glob:
                if len(path.name.split(".")[0]) != 16:
                    continue
                measurements.append(
                    Measurement(
                        path=path,
                        type=MeasurementType(path.name[:2]),
                        lidar_name=lidar_name,
                    )
                )
            return measurements
    from lidarpy.plot.quicklook import BoundsType, quicklook_from_file
    from lidarpy.utils.types import LidarName, MeasurementType
    from lidarpy.utils.utils import LIDAR_INFO, licel_to_datetime

    LIDAR_BACKEND = "lidarpy"
except ImportError:
    LIDAR_BACKEND = "missing"

    def _missing_lidarpy(*args, **kwargs):
        raise RuntimeError(
            "LIDAR processing requires the 'atmolidarpy' distribution "
            "providing the import package 'lidarpy'."
        )

    class Measurement:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            _missing_lidarpy()

    BoundsType = object
    LIDAR_INFO = {"metadata": {"name2nick": {}, "nick2name": {}}}
    LidarName = _missing_lidarpy
    MeasurementType = _missing_lidarpy
    find_nearest_filepath = _missing_lidarpy
    licel_to_datetime = _missing_lidarpy
    quicklook_from_file = _missing_lidarpy
    read_yaml = _missing_lidarpy
    to_measurements = _missing_lidarpy

__all__ = [
    "BoundsType",
    "LIDAR_BACKEND",
    "LIDAR_INFO",
    "LidarName",
    "Measurement",
    "MeasurementType",
    "find_nearest_filepath",
    "licel_to_datetime",
    "quicklook_from_file",
    "read_yaml",
    "to_measurements",
]
