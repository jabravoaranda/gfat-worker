from celery import shared_task

import os
import inspect
from time import sleep
from pathlib import Path
from typing import Any, Tuple
from loguru import logger
from datetime import datetime, time, date, timedelta

from lidar_backend import (
    BoundsType,
    LIDAR_BACKEND,
    LIDAR_INFO,
    LidarName,
    Measurement,
    MeasurementType,
    find_nearest_filepath,
    licel_to_datetime,
    quicklook_from_file,
    read_yaml,
    to_measurements,
)


try:
    import lidarpy.scc as lidarpy_scc
    from lidarpy.scc import scc_access
    from lidarpy.scc.plot.scc_zip import SCC_zipfile
    from lidarpy.scc.transfer import check_measurement_id_in_scc
    from lidarpy.scc.licel2scc import licel2scc, licel2scc_depol

    SCC_CONFIG_DIR = Path(lidarpy_scc.__file__).parent / "scc_configFiles"
except ImportError:
    class _MissingSccBackend:
        def __getattr__(self, name: str):
            raise RuntimeError(
                "SCC tasks require 'atmolidarpy' with the import package "
                "'lidarpy.scc'."
            )

    def check_measurement_id_in_scc(*args, **kwargs):
        raise RuntimeError(
            "SCC tasks require 'atmolidarpy' with the import package 'lidarpy.scc'."
        )

    class SCC_zipfile:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "SCC plotting requires 'atmolidarpy' with the import package "
                "'lidarpy.scc'."
            )

    scc_access = _MissingSccBackend()
    licel2scc = _MissingSccBackend()
    licel2scc_depol = _MissingSccBackend()
    SCC_CONFIG_DIR = Path("/usr/src/app/scc_configFiles")

RAW_DIR = Path(os.environ.get("RAW_DIR", "/mnt/RAW/UGR"))
PRODUCTS_DIR = Path(os.environ.get("PRODUCTS_DIR", "/mnt/PRODUCTS/UGR"))
SCC_CONFIG_DIR = Path(os.environ.get("SCC_CONFIG_DIR", SCC_CONFIG_DIR))
INFO_SCC_CONFIG_PATH = Path(
    os.environ.get("INFO_SCC_CONFIG_PATH", "/usr/src/app/info_scc_user.yml")
)

logger.info(f"Using {LIDAR_BACKEND} as lidar processing backend.")


def measurement_to_nc(measurement: Measurement, target_date: date, output_dir: Path):
    """Convert a measurement to NetCDF across supported lidarpy signatures."""
    to_nc_parameters = inspect.signature(measurement.to_nc).parameters
    kwargs: dict[str, Any] = {"output_dir": output_dir}

    if "target_date" in to_nc_parameters:
        kwargs["target_date"] = target_date
    elif "by_dates" in to_nc_parameters:
        kwargs["by_dates"] = True

    return measurement.to_nc(**kwargs)


def cleanup_measurement_tmp(measurement: Measurement) -> None:
    """Remove temporary extraction data without relying on lidarpy internals."""
    remove_tmp = getattr(measurement, "remove_tmp_unzipped_dir", None)
    if remove_tmp is None:
        return

    remove_tmp()
    measurement_path = getattr(measurement, "path", None)
    if measurement_path is not None:
        logger.info(f"Temporary files removed for {Path(measurement_path).name}.")
    else:
        logger.info("Temporary files removed for measurement.")


def parse_time_interval(ini_interval: str, end_interval: str) -> Tuple[time, time]:
    def parse_time_value(value: str) -> time:
        if len(value.split(":")) == 2:
            value = f"{value}:00"
        return datetime.strptime(value, "%H:%M:%S").time()

    return parse_time_value(ini_interval), parse_time_value(end_interval)


def get_measurement_files_within_period(
    measurement: Measurement, period: tuple[datetime, datetime]
) -> list[Path]:
    """Return extracted Licel files from a measurement within a datetime period."""
    if hasattr(measurement, "get_filenames_within_datetime_slice"):
        filenames = measurement.get_filenames_within_datetime_slice(
            slice(period[0], period[1])
        )
        if not filenames:
            return []
        filepaths = measurement.get_filepaths(pattern_or_list=filenames)
    else:
        filepaths = measurement.get_filepaths(within_period=period)

    if not filepaths:
        return []
    return sorted(filepaths)


def get_measurement_files_pattern(measurement: Measurement) -> str:
    """Extract a measurement and return a glob pattern accepted by licel2scc."""
    filepaths = measurement.get_filepaths()
    if not filepaths:
        raise FileNotFoundError(f"No files found in {measurement.path}.")

    filepaths = sorted(filepaths)
    if len(filepaths) == 1:
        return filepaths[0].as_posix()

    parents = {file_.parent for file_ in filepaths}
    if len(parents) == 1:
        return (parents.pop() / "*.*").as_posix()

    common_dir = Path(os.path.commonpath([file_.as_posix() for file_ in filepaths]))
    return (common_dir / "*" / "*.*").as_posix()


@shared_task
def task_nc_convert(
    lidar_name: str,
    target_date: str | None = None,
    measurement_type: str = 'RS',
    raw_dir: Path = RAW_DIR,
    products_dir: Path = PRODUCTS_DIR,
):
    def nc_convert(lidar_name: str,
                   target_date: str | date | None = None,
                   raw_dir: str | Path = RAW_DIR,
                   products_dir: str | Path = PRODUCTS_DIR
                   ) -> str:

        if isinstance(raw_dir, str):
            raw_dir = Path(raw_dir)

        if not raw_dir.exists():
            raise FileNotFoundError(f"{raw_dir} does not exist.")

        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        lidar = LidarName(lidar_name.lower())

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        date_raw_dir = (
            raw_dir
            / lidar.value
            / f"{target_date.year}"
            / f"{target_date.month:02}"
            / f"{target_date.day:02}"
        )

        if date_raw_dir.exists():
            logger.info(f"{target_date} directory found in ../{lidar.value}.")
            measurements = to_measurements(
                lidar_name=lidar.value, glob=date_raw_dir.glob(f"{measurement_type}*"))
            for measurement in measurements:
                logger.info(f"Converting {measurement.path.name} to nc.")
                measurement_to_nc(measurement, target_date, products_dir)
                cleanup_measurement_tmp(measurement)
                if measurement.has_linked_dc:
                    logger.info(
                        f"Converting {measurement.dc.path.name} to nc.")
                    measurement_to_nc(measurement.dc, target_date, products_dir)
                    cleanup_measurement_tmp(measurement.dc)
        else:
            logger.info(
                f"{target_date} directory not found in ../{lidar.value}.")
            previous_day = target_date-timedelta(days=1)
            logger.info(f"Searching in previous day: {previous_day}.")
            date_raw_dir = (
                raw_dir
                / lidar.value
                / f"{previous_day.year}"
                / f"{previous_day.month:02}"
                / f"{previous_day.day:02}"
            )
            if not date_raw_dir.exists():
                return f"Neither {target_date} nor {previous_day} directory found in ../{lidar.value}."
            else:
                logger.info(f"Previous day directory found: {previous_day}")

            measurements = to_measurements(
                lidar_name=lidar.value, glob=date_raw_dir.glob("RS*"))
            for measurement in measurements:
                logger.info(f"Converting {measurement.path.name} to nc.")
                measurement_to_nc(measurement, target_date, products_dir)
                cleanup_measurement_tmp(measurement)
                if measurement.has_linked_dc:
                    logger.info(
                        f"Converting {measurement.dc.path.name} to nc.")
                    measurement_to_nc(measurement.dc, target_date, products_dir)
                    cleanup_measurement_tmp(measurement.dc)

        return f"nc files created in ../{lidar.value}/1a/{target_date.year}/{target_date.month:02}/{target_date.day:02}."

    message = nc_convert(
        lidar_name=lidar_name,
        target_date=target_date,
        raw_dir=raw_dir,
        products_dir=products_dir,
    )
    return message


@shared_task
def task_quicklook(
    lidar_name: str,
    channel: str,
    min_scale_bound: str | None = None,
    max_scale_bound: str | None = None,
    target_date: str | None = None,
    products_dir: Path = PRODUCTS_DIR,
):
    def quicklook(
        lidar_name: str,
        channel: str,
        target_date: str | date | None = None,
        products_dir: str | Path = PRODUCTS_DIR,
        scale_bounds: BoundsType = 'auto'
    ) -> str:
        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        if not products_dir.exists():
            raise FileNotFoundError(f"{products_dir} does not exist.")

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        datestr = target_date.strftime("%Y%m%d")
        year, month, day = target_date.year, target_date.month, target_date.day

        data_dir = (
            products_dir / lidar_name / "1a" /
            f"{year:04}" / f"{month:02}" / f"{day:02}"
        )
        lidarnick = LIDAR_INFO["metadata"]["name2nick"][lidar_name]
        files = [
            *data_dir.glob(f"{lidarnick}_1a_Prs_rs_*{year:04}{month:02}{day:02}.nc")]

        if not files:
            return f"No files found in {data_dir}."
        if len(list(files)) > 1:
            return f"More than one RS lidar netcdf file found in {data_dir}."

        quicklook_dir = products_dir / lidar_name / "quicklooks" / channel
        quicklook_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"{files[0].name} measurements found in {data_dir}.")

        quicklook_from_file(
            filepath=files[0], channels=[
                channel], output_dir=quicklook_dir, scale_bounds=scale_bounds
        )
        quicklook_file = f"quicklook_{lidarnick}_{channel}_{datestr}.png"
        return f"{quicklook_file} created."

    if min_scale_bound is None or max_scale_bound is None:
        scale_bounds = 'auto'
    else:
        scale_bounds = (float(min_scale_bound), float(max_scale_bound))

    message = quicklook(
        lidar_name=lidar_name,
        channel=channel,
        target_date=target_date,
        products_dir=products_dir,
        scale_bounds=scale_bounds
    )
    return message


@shared_task
def task_convert_scc(
    lidar_name: str,
    scc_id: int,
    ini_interval: str,
    end_interval: str,
    temperature: float = 20.0,
    pressure: float = 1013.25,
    target_date: str | None = None,
    raw_dir: Path = RAW_DIR,
    products_dir: Path = PRODUCTS_DIR,
):
    interval = parse_time_interval(ini_interval, end_interval)
    
    def convert_scc(
        lidar_name: str,
        scc_id: int,
        temperature: float = 20.0,
        pressure: float = 1013.25,
        target_date: str | date | None = None,
        interval: Tuple[time, time] =
            (time(3, 15), time(3, 45)),
        raw_dir: str | Path = RAW_DIR,
        products_dir: str | Path = PRODUCTS_DIR,
        **kwargs,
    ) -> list[str] | str:

        if isinstance(raw_dir, str):
            raw_dir = Path(raw_dir)

        if not raw_dir.exists():
            raise FileNotFoundError(f"{raw_dir} does not exist.")

        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        scc_id = int(scc_id)

        logger.info(
            f"Launching SCC conversion for {lidar_name} on {target_date}.")

        year, month, day = target_date.year, target_date.month, target_date.day

        nc_scc_files = []

        nc_scc_dir = (
            products_dir
            / f"{lidar_name}"
            / "scc"
            / f"scc{scc_id}"
            / f"{year:04}"
            / f"{month:02}"
            / f"{day:02}"
        )
        nc_scc_dir.mkdir(parents=True, exist_ok=True)

        scc_config_dir = Path(
            kwargs.get(
                "scc_config_dir", SCC_CONFIG_DIR
            )
        )
        lidar_nick = LIDAR_INFO["metadata"]["name2nick"][lidar_name]
        scc_config_fn = find_nearest_filepath(
            scc_config_dir,
            f"{lidar_nick}_parameters_scc_{scc_id}_*.py",
            4,
            target_date,
            and_previous=True,
        )
        logger.info(f"Using {scc_config_fn.name} for SCC conversion.")

        # Define custom class for regular lidar measurements
        CustomLidarMeasurement = licel2scc.create_custom_class(
            scc_config_fn.absolute().as_posix(),
            use_id_as_name=True,
            temperature=temperature,
            pressure=pressure,
        )

        data_dir = (
            raw_dir
            / f"{lidar_name}"
            / f"{target_date.year:04}"
            / f"{target_date.month:02}"
            / f"{target_date.day:02}"
        )

        if data_dir.exists():
            logger.info(f"{target_date} directory found in ../{lidar_name}.")
            measurements = to_measurements(lidar_name=lidar_name, glob=data_dir.glob(
                f"RS*"
            )
            )
            if measurements is not None:
                logger.info(
                    f"Measurements found on {target_date}: {len(measurements)}")
            else:
                logger.info(f"No measurements found in {target_date}.")
        else:
            logger.info(
                f"{target_date} directory not found in ../{lidar_name}.")
            previous_day = target_date-timedelta(days=1)
            logger.info(f"Searching in previous day: {previous_day}.")
            data_dir = (
                raw_dir
                / lidar_name
                / f"{previous_day.year}"
                / f"{previous_day.month:02}"
                / f"{previous_day.day:02}"
            )
            if data_dir.exists():
                logger.info(f"Previous day directory found: {previous_day}")
                measurements = to_measurements(lidar_name=lidar_name, glob=data_dir.glob(
                    f"RS*"
                )
                )
                if measurements is not None:
                    logger.info(
                        f"Measurements found in {previous_day}: {len(measurements)}")
                else:
                    logger.info(
                        f"{len(measurements)} measurements found in {data_dir}.")
            else:
                logger.info(
                    f"Neither {target_date} nor {previous_day} directory found in ../{lidar_name}.")

        period_tuple = (datetime.combine(
            target_date, interval[0]), datetime.combine(target_date, interval[1]))

        for measurement in measurements:
            file_set = get_measurement_files_within_period(
                measurement, period_tuple
            )

            if len(file_set) < 30:
                logger.warning(
                    f"Conversion aborted: less than 30 files found in {measurement.path}.")
                continue

            logger.info(
                f"Interval {interval[0].strftime('%H:%M')}-{interval[1].strftime('%H:%M')} has {len(file_set)} files."
            )

            # sort file_set
            file_set = sorted(file_set)

            # Get initial hour from first file in file_set
            first_hour = licel_to_datetime(file_set[0].name)
            measurement_id = f"{year:04}{month:02}{day:02}gra{first_hour.strftime('%H%M')}"
            if (nc_scc_dir / f"{measurement_id}.nc").exists():
                logger.warning(
                        f"{measurement_id} already exists.")
                break
            logger.info(f"Creating {measurement_id}.nc.")

            rs_files_slot = sorted([file_.as_posix()
                                    for file_ in file_set])

            if measurement.has_linked_dc:
                logger.info(f"Found coincident DC measurement: {measurement.dc.path.name}.")
            else:
                try:
                    dc_measurement = to_measurements(
                        lidar_name=lidar_name, glob=data_dir.glob("DC*"))[0]
                    measurement._dc = dc_measurement
                    logger.info(
                        f"Found non-coincident DC measurement: {measurement.dc.path.name}."
                    )
                except FileNotFoundError:
                    logger.warning(
                        f"No DC measurements found in {data_dir}.")
                    continue

            if measurement.dc.is_zip:
                dc_files_patt = get_measurement_files_pattern(measurement.dc)
            else:
                dc_files_patt = measurement.dc.path.as_posix()

            licel2scc.convert_to_scc(
                CustomLidarMeasurement,
                rs_files_slot,
                dc_files_patt,
                measurement_id,
                output_dir=nc_scc_dir,
            )
            if not (nc_scc_dir / f"{measurement_id}.nc").exists():
                logger.warning(
                    f"Error converting {measurement_id} to SCC.")
                continue
            else:
                logger.info(f"{measurement_id}.nc created.")
                nc_scc_files.append(nc_scc_dir / f"{measurement_id}.nc")
        if nc_scc_files == []:
            return f"No SCC files created for {lidar_name} on {target_date}."
        return [nc.name for nc in nc_scc_files]

    message = convert_scc(
        lidar_name=lidar_name,
        scc_id=scc_id,
        temperature=temperature,
        pressure=pressure,
        interval=interval,
        target_date=target_date,
        raw_dir=raw_dir,
        products_dir=products_dir,
        **{
            "scc_config_dir": SCC_CONFIG_DIR
        },
    )
    return message


@shared_task
def task_convert_scc_dp(
    lidar_name: str,
    scc_id: int,
    target_date: str | None = None,
    raw_dir: Path = RAW_DIR,
    products_dir: Path = PRODUCTS_DIR,
):
    def convert_scc_dp(
        lidar_name: str,
        scc_id: int,
        temperature: float = 20.0,
        pressure: float = 1013.25,
        target_date: str | date | None = None,
        licel_timezone: str = "UTC",
        raw_dir: str | Path = RAW_DIR,
        products_dir: str | Path = PRODUCTS_DIR,
        **kwargs,
    ) -> list[str] | str:

        if isinstance(raw_dir, str):
            raw_dir = Path(raw_dir)

        if not raw_dir.exists():
            raise FileNotFoundError(f"{raw_dir} does not exist.")

        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        scc_id = int(scc_id)
        year, month, day = target_date.year, target_date.month, target_date.day
        date_str = target_date.strftime("%Y%m%d")

        scc_config_dir = Path(
            kwargs.get("scc_config_dir", SCC_CONFIG_DIR)
        )
        scc_config_fn = find_nearest_filepath(
            scc_config_dir,
            f"alh_parameters_scc_{scc_id}_*.py",
            4,
            datetime.combine(target_date, time(0, 0)),
            and_previous=True,
        )
        logger.info(f"Using {scc_config_fn.name} for SCC conversion.")

        CustomLidarMeasurement = licel2scc_depol.create_custom_class(
            scc_config_fn.absolute().as_posix(),
            use_id_as_name=True,
            temperature=temperature,
            pressure=pressure,
        )

        # Find DP measurements
        data_dir = raw_dir / lidar_name / \
            f"{year}" / f"{month:02}" / f"{day:02}"
        measurements = to_measurements(
            lidar_name=lidar_name, glob=data_dir.glob(f"DP_{date_str}*.zip"))
        if not measurements:
            logger.warning(f"No measurements found in {data_dir}.")
            return f"No measurements found in {data_dir}."
        logger.info(f"{len(measurements)} measurements found in {data_dir}.")
        output_paths = []
        for measurement in measurements:
            if measurement.is_zip:
                measurement.extract_zip()
                if measurement.unzipped_path is not None:
                    plus45_files = [
                        file_.as_posix()
                        for file_ in measurement.unzipped_path.rglob(f"{date_str}/+45/*.*")
                    ]
                    minus45_files = [
                        file_.as_posix()
                        for file_ in measurement.unzipped_path.rglob(f"{date_str}/-45/*.*")
                    ]
                else:
                    raise ValueError(f"Error extracting {measurement.path}.")
            else:
                plus45_files = [
                    file_.as_posix()
                    for file_ in measurement.path.rglob(f"{date_str}/+45/*.*")
                ]
                minus45_files = [
                    file_.as_posix()
                    for file_ in measurement.path.rglob(f"{date_str}/-45/*.*")
                ]

            if plus45_files == []:
                raise Exception("No P45 files found")

            if plus45_files == []:
                raise Exception("No N45 files found")

            if measurement.has_linked_dc:
                dc_tmp_path = measurement.dc_path
                if dc_tmp_path is not None:
                    dc_measurement = to_measurements(
                        lidar_name=lidar_name, glob=data_dir.glob(dc_tmp_path.name))[0]
                    if dc_measurement.is_zip:
                        if dc_measurement.unzipped_path is not None:
                            dark_files = [
                                file_.as_posix()
                                for file_ in dc_measurement.unzipped_path.rglob(
                                    f"{date_str}/[RD]*.*"
                                )
                            ]
                        else:
                            raise ValueError(
                                f"Error extracting {dc_measurement.path.name}.")
                    else:
                        dark_files = [
                            file_.as_posix()
                            for file_ in dc_measurement.path.rglob(f"{date_str}/[RD]*.*")
                        ]
            hour_str = measurement.path.name.split(".")[0].split("_")[-1]
            measurement_id = f"{year:04}{month:02}{day:02}gra{hour_str}"
            output_path = (
                products_dir
                / lidar_name
                / "scc"
                / f"scc{scc_id}"
                / f"{year}"
                / f"{month:02}"
                / f"{day:02}"
                / f"{measurement_id}.nc"
            )

            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)

            CustomLidarMeasurement = licel2scc_depol.create_custom_class(
                scc_config_fn, True, temperature, pressure, licel_timezone
            )

            CustomDarkMeasurement = licel2scc_depol.create_custom_dark_class(
                scc_config_fn, True, temperature, pressure, licel_timezone
            )

            measurement = CustomLidarMeasurement(plus45_files, minus45_files)

            if dark_files:
                measurement.dark_measurement = CustomDarkMeasurement(
                    dark_files)  # type: ignore
            else:
                raise Exception("No dark measurement files found.")

            try:
                measurement = measurement.subset_by_scc_channels()
            except ValueError as err:
                raise err

            # Save the netcdf
            measurement.set_measurement_id(output_path.name.split(".")[0])
            measurement.save_as_SCC_netcdf(output_dir=output_path.parent)
            output_paths.append(output_path.absolute().as_posix())
        return output_paths

    message = convert_scc_dp(
        lidar_name=lidar_name,
        scc_id=scc_id,
        temperature=20.0,
        pressure=1013.25,
        target_date=target_date,
        raw_dir=raw_dir,
        products_dir=products_dir,
        **{
            "scc_config_dir": SCC_CONFIG_DIR
        },
    )
    return message


@shared_task
def task_send_to_scc(
    lidar_name: str,
    scc_id: int,
    target_date: str | None = None,
    products_dir: Path = PRODUCTS_DIR,
):
    def send_to_scc(
        lidar_name: str,
        scc_id: int,
        info_scc_config_path: str | Path,
        target_date: str | date | None = None,
        products_dir: str | Path = PRODUCTS_DIR,
        **kwargs,
    ) -> list[str] | str:

        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        # Check if the environment variable is set
        if isinstance(info_scc_config_path, str):
            info_scc_config_path = Path(info_scc_config_path)

        config_path = info_scc_config_path

        if not config_path.exists():
            raise ValueError(
                "The environment variable 'SCC_CONFIG_FILE' is not set in the .env"
            )

        logger.info(f"Using {config_path} for SCC conversion.")

        # Construct the file path
        SCC_INFO = read_yaml(config_path)
        SCC_SERVER_SETTINGS = SCC_INFO["server_settings"]

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        year, month, day = target_date.year, target_date.month, target_date.day

        scc_dir = (
            products_dir
            / lidar_name
            / "scc"
            / f"scc{scc_id}"
            / f"{year:04}"
            / f"{month:02}"
            / f"{day:02}"
        )
        if len(list(scc_dir.glob("*.nc"))) == 0:
            directory = f"../{lidar_name}/scc/scc{scc_id}/{year:04}/{month:02}/{day:02}"
            return f"No files found in {directory}."
        else:
            files = scc_dir.glob("*.nc")

        track_files = []
        for file_ in files:
            logger.info(
                f"Launching SCC conversion for {lidar_name} on {target_date}.")
            measurement_id = file_.name.replace(".nc", "")

            scc_obj = scc_access.SCC(
                tuple(SCC_SERVER_SETTINGS["basic_credentials"]),
                SCC_SERVER_SETTINGS["output_dir"],
                SCC_SERVER_SETTINGS["base_url"],
            )

            measurement_exists, _ = check_measurement_id_in_scc(
                SCC_SERVER_SETTINGS, measurement_id
            )

            if measurement_exists:
                logger.info(
                    f"Measurement {measurement_id} already exists in SCC: {measurement_exists}."
                )
                track_files.append(f"{measurement_id}=found")
                continue

            try:
                scc_obj.login(SCC_SERVER_SETTINGS["website_credentials"])
                measurement_id_from_server = scc_obj.upload_file(
                    filename=file_, system_id=scc_id
                )
            except Exception as exc:
                logger.exception(f"Error uploading {measurement_id}.nc to SCC.")
                track_files.append(
                    f"{measurement_id}=upload_error:{type(exc).__name__}:"
                    f"{exc}"
                )
                continue
            finally:
                try:
                    scc_obj.logout()
                except Exception:
                    logger.warning("Could not log out from SCC cleanly.")

            if not measurement_id_from_server:
                logger.warning(f"Error uploading {measurement_id}.nc to SCC.")
                track_files.append(f"{measurement_id}=error")
                continue

            logger.info(f"{measurement_id}.nc uploaded to SCC.")
            track_files.append(f"{measurement_id}=uploaded")
        return track_files

    message = send_to_scc(
        lidar_name=lidar_name,
        scc_id=scc_id,
        info_scc_config_path=INFO_SCC_CONFIG_PATH,
        target_date=target_date,
        products_dir=products_dir,
    )
    return message


@shared_task
def task_download_from_scc(
    lidar_name: str,
    scc_id: int,
    target_date: str | None = None,
    products_dir: Path = PRODUCTS_DIR,
):
    def download_from_scc(
        lidar_name: str,
        scc_id: int,
        info_scc_config_path: str | Path,
        target_date: str | date | None = None,
        products_dir: str | Path = PRODUCTS_DIR,
        **kwargs,
    ) -> list[str] | str:

        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        # Check if the environment variable is set
        if isinstance(info_scc_config_path, str):
            info_scc_config_path = Path(info_scc_config_path)

        config_path = info_scc_config_path

        if not config_path.exists():
            raise ValueError(
                "The environment variable 'SCC_CONFIG_FILE' is not set in the .env"
            )

        logger.info(f"Using {config_path} for SCC conversion.")

        # Construct the file path
        SCC_INFO = read_yaml(config_path)
        SCC_SERVER_SETTINGS = SCC_INFO["server_settings"]

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        year, month, day = target_date.year, target_date.month, target_date.day

        scc_dir = (
            products_dir
            / lidar_name
            / "scc"
            / f"scc{scc_id}"
            / f"{year:04}"
            / f"{month:02}"
            / f"{day:02}"
        )

        product_scc_dir = scc_dir / "products"
        product_scc_dir.mkdir(parents=True, exist_ok=True)
        SCC_SERVER_SETTINGS["output_dir"] = product_scc_dir

        files = [*scc_dir.rglob(f"{year:04}{month:02}{day:02}*.nc")]
        if len(files) == 0:
            return f"No files downloaded."
        logger.info(f"{len(files)} files to be downloaded.")
        track_files = []
        for file_ in scc_dir.glob(f"{year:04}{month:02}{day:02}*.nc"):
            logger.info(f"Downloading {file_.name} from SCC.")
            measurement_id = file_.name.replace(".nc", "")

            scc_obj = scc_access.SCC(
                tuple(SCC_SERVER_SETTINGS["basic_credentials"]),
                SCC_SERVER_SETTINGS["output_dir"],
                SCC_SERVER_SETTINGS["base_url"],
            )

            scc_obj.login(SCC_SERVER_SETTINGS["website_credentials"])

            # Manejo de reintentos
            retries = 5
            for attempt in range(retries):
                try:
                    scc_obj.monitor_processing(measurement_id)
                    track_files.append(f"{file_.name}=downloaded")
                    logger.info(f"{file_.name} products downloaded from SCC.")
                    break
                except TimeoutError:
                    if attempt < retries - 1:
                        # Esperar un tiempo antes de reintentar
                        sleep(60)
                    else:
                        logger.warning(
                            f"Process was queued too long after {retries} attempts."
                        )
                        track_files.append(f"{file_.name}=failed")
                        continue

            scc_obj.logout()

        return track_files

    message = download_from_scc(
        lidar_name=lidar_name,
        scc_id=scc_id,
        info_scc_config_path=INFO_SCC_CONFIG_PATH,
        target_date=target_date,
        products_dir=products_dir,
    )
    return message


@shared_task
def task_plot_scc(
    lidar_name: str,
    scc_id: int,
    target_date: str | None = None,
    products_dir: Path = PRODUCTS_DIR,
):
    def plot_scc(
        lidar_name: str,
        scc_id: int,
        target_date: str | date | None = None,
        products_dir: str | Path = PRODUCTS_DIR
    ) -> list[str] | str:

        def flatten_list(nested_list):
            flattened = []
            for item in nested_list:
                if isinstance(item, list):
                    flattened.extend(flatten_list(item))
                else:
                    flattened.append(item)
            return flattened

        if isinstance(products_dir, str):
            products_dir = Path(products_dir)

        if not products_dir.exists():
            raise FileNotFoundError(f"{products_dir} does not exist.")

        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        year, month, day = target_date.year, target_date.month, target_date.day

        scc_dir = (
            products_dir
            / lidar_name
            / "scc"
            / f"scc{scc_id}"
            / f"{year:04}"
            / f"{month:02}"
            / f"{day:02}"
            / "products"
        )

        if not scc_dir.exists():
            return f"../{lidar_name}/scc/scc{scc_id}/{year:04}/{month:02}/{day:02} does not exist."

        logger.info(f"Searching for products in {scc_dir}.")
        products = [*scc_dir.glob("*.zip")]
        logger.info(
            f"{len(products)} products found in ../{lidar_name}/scc/scc{scc_id}/{year:04}/{month:02}/{day:02}.")

        # Plotting scc results
        plot_scc_dir = scc_dir / "plots"
        plot_scc_dir.mkdir(parents=True, exist_ok=True)

        if not products:
            return f"No SCC files found in ../{lidar_name}/scc/scc{scc_id}/{year:04}/{month:02}/{day:02}."
        plot_paths = []
        for product in products:
            logger.info(f"Plotting {product.name}.")
            try:
                scc_zip = SCC_zipfile(product)
            except Exception as e:
                logger.warning(f"Error reading {product} as SCC zipfile.")
                continue
            plot_paths_ = scc_zip.plot(
                output_dir=plot_scc_dir, dpi=150, range_limits=(0, 10)
            )
            if isinstance(plot_paths_, list):
                plot_paths.extend(plot_paths_)
            else:
                plot_paths.append(plot_paths_)

        flattened_list = flatten_list(plot_paths)

        plot_names = [plot.name for plot in flattened_list]
        return plot_names

    message = plot_scc(
        lidar_name=lidar_name,
        scc_id=scc_id,
        target_date=target_date,
        products_dir=products_dir,
    )
    return message


@shared_task
def remove_temp_files():
    tmp_files = [*Path('/usr/src/app').rglob('tmp_unzipped_*')]
    for tmp_ in tmp_files:
        import shutil
        shutil.rmtree(tmp_)
