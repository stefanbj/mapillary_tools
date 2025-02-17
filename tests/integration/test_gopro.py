import json
import os
import subprocess
import typing as T
from pathlib import Path

import py.path
import pytest

from .fixtures import EXECUTABLE, is_ffmpeg_installed, setup_config, setup_upload


IMPORT_PATH = "tests/data/gopro_data"

expected_descs: T.List[T.Any] = [
    {
        "MAPAltitude": 9540.24,
        "MAPCaptureTime": "2019_11_18_15_41_12_354",
        "MAPCompassHeading": {
            "TrueHeading": 123.93587938690177,
            "MagneticHeading": 123.93587938690177,
        },
        "MAPLatitude": 42.0266244,
        "MAPLongitude": -129.2943386,
        "filename": "hero8.mp4/hero8_NA_000001.jpg",
    },
    {
        "MAPAltitude": 7112.573717404068,
        "MAPCaptureTime": "2019_11_18_15_41_14_354",
        "MAPCompassHeading": {
            "TrueHeading": 140.8665026186285,
            "MagneticHeading": 140.8665026186285,
        },
        "MAPLatitude": 35.33318621742755,
        "MAPLongitude": -126.85929159704702,
        "filename": "hero8.mp4/hero8_NA_000002.jpg",
    },
    {
        "MAPAltitude": 7463.642846094319,
        "MAPCaptureTime": "2019_11_18_15_41_16_354",
        "MAPCompassHeading": {
            "TrueHeading": 138.44255851085705,
            "MagneticHeading": 138.44255851085705,
        },
        "MAPLatitude": 36.32681619054138,
        "MAPLongitude": -127.18475264566939,
        "filename": "hero8.mp4/hero8_NA_000003.jpg",
    },
    {
        "MAPAltitude": 6909.8168472111465,
        "MAPCaptureTime": "2019_11_18_15_41_18_354",
        "MAPCompassHeading": {
            "TrueHeading": 142.23462669862568,
            "MagneticHeading": 142.23462669862568,
        },
        "MAPLatitude": 34.7537270390268,
        "MAPLongitude": -126.65905680405231,
        "filename": "hero8.mp4/hero8_NA_000004.jpg",
    },
    {
        "MAPAltitude": 7212.594480737465,
        "MAPCaptureTime": "2019_11_18_15_41_20_354",
        "MAPCompassHeading": {
            "TrueHeading": 164.70819093235514,
            "MagneticHeading": 164.70819093235514,
        },
        "MAPLatitude": 35.61583820322709,
        "MAPLongitude": -126.93688762007304,
        "filename": "hero8.mp4/hero8_NA_000005.jpg",
    },
    {
        "MAPAltitude": 7274.361994963208,
        "MAPCaptureTime": "2019_11_18_15_41_22_354",
        "MAPCompassHeading": {
            "TrueHeading": 139.71549328876722,
            "MagneticHeading": 139.71549328876722,
        },
        "MAPLatitude": 35.79255093264954,
        "MAPLongitude": -126.98833423074615,
        "filename": "hero8.mp4/hero8_NA_000006.jpg",
    },
]


@pytest.fixture
def setup_data(tmpdir: py.path.local):
    data_path = tmpdir.mkdir("data")
    source = py.path.local(IMPORT_PATH)
    source.copy(data_path)
    yield data_path
    if tmpdir.check():
        tmpdir.remove(ignore_errors=True)


@pytest.fixture
def setup_envvars():
    os.environ["MAPILLARY_TOOLS_GOPRO_GPS_FIXES"] = "0,2,3"
    os.environ["MAPILLARY_TOOLS_GOPRO_MAX_DOP100"] = "100000"
    os.environ["MAPILLARY_TOOLS_GOPRO_GPS_PRECISION"] = "10000000"
    yield
    del os.environ["MAPILLARY_TOOLS_GOPRO_GPS_FIXES"]
    del os.environ["MAPILLARY_TOOLS_GOPRO_MAX_DOP100"]
    del os.environ["MAPILLARY_TOOLS_GOPRO_GPS_PRECISION"]


@pytest.mark.usefixtures("setup_config")
@pytest.mark.usefixtures("setup_upload")
@pytest.mark.usefixtures("setup_envvars")
def test_process_gopro_hero8(
    setup_data: py.path.local,
):
    if not is_ffmpeg_installed:
        pytest.skip("skip because ffmpeg not installed")
    video_path = setup_data.join("hero8.mp4")
    # this sample hero8.mp4 doesn't have any good GPS points,
    # so we do not filter out bad GPS points
    x = subprocess.run(
        f"{EXECUTABLE} video_process --video_sample_interval=2 --video_sample_distance=-1 --geotag_source=gopro_videos {str(video_path)}",
        shell=True,
    )
    assert x.returncode == 0, x.stderr
    desc_path = setup_data.join("mapillary_sampled_video_frames").join(
        "mapillary_image_description.json"
    )
    assert desc_path.exists()
    with open(desc_path) as fp:
        descs = json.load(fp)
    for expected, actual in zip(expected_descs, descs):
        assert abs(expected["MAPLatitude"] - actual["MAPLatitude"]) < 0.0000001
        assert abs(expected["MAPLongitude"] - actual["MAPLongitude"]) < 0.0000001
        assert expected["MAPCaptureTime"] == actual["MAPCaptureTime"]
        assert abs(expected["MAPAltitude"] - actual["MAPAltitude"]) < 0.001
        assert (
            abs(
                expected["MAPCompassHeading"]["TrueHeading"]
                - actual["MAPCompassHeading"]["TrueHeading"]
            )
            < 0.001
        )
        assert (
            abs(
                expected["MAPCompassHeading"]["MagneticHeading"]
                - actual["MAPCompassHeading"]["MagneticHeading"]
            )
            < 0.001
        )
        assert Path(actual["filename"]).is_file(), actual["filename"]
        assert Path(actual["filename"]).as_posix().endswith(expected["filename"])
        assert "MAPSequenceUUID" in actual
