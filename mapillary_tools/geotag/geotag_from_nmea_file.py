import datetime
import typing as T
from pathlib import Path

import pynmea2

from .. import geo

from .geotag_from_gpx import GeotagFromGPX


class GeotagFromNMEAFile(GeotagFromGPX):
    def __init__(
        self,
        images: T.Sequence[Path],
        source_path: Path,
        use_gpx_start_time: bool = False,
        offset_time: float = 0.0,
    ):
        points = get_lat_lon_time_from_nmea(source_path)
        super().__init__(
            images,
            points,
            use_gpx_start_time=use_gpx_start_time,
            offset_time=offset_time,
        )


def get_lat_lon_time_from_nmea(nmea_file: Path) -> T.List[geo.Point]:
    with nmea_file.open("r") as f:
        lines = f.readlines()
        lines = [line.rstrip("\n\r") for line in lines]

    # Get initial date
    for line in lines:
        if "GPRMC" in line:
            data = pynmea2.parse(line)
            date = data.datetime.date()
            break

    # Parse GPS trace
    points = []
    for line in lines:
        if "GPRMC" in line:
            data = pynmea2.parse(line)
            date = data.datetime.date()

        if "$GPGGA" in line:
            data = pynmea2.parse(line)
            dt = datetime.datetime.combine(date, data.timestamp)
            lat, lon, alt = data.latitude, data.longitude, data.altitude
            points.append(
                geo.Point(
                    time=geo.as_unix_time(dt), lat=lat, lon=lon, alt=alt, angle=None
                )
            )

    points.sort()
    return points
