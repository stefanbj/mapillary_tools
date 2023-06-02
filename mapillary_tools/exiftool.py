# pyre-ignore-all-errors[5, 24]

import logging
import os
import subprocess
import sys
import typing as T
from pathlib import Path
import tempfile

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict

LOG = logging.getLogger(__name__)

class ExiftoolNotFoundError(Exception):
    pass

class EXIFTOOL:
    def __init__(
        self,
        exiftool_path: str = "exiftool",
        exiftoolk_path: str = "exiftoolk(-k)",
        gpx_fmt: str = None,
        stderr: T.Optional[int] = None,
    ) -> None:
        """
        exiftool_path: path to exiftool binary
        exiftoolk_path: path to exiftool(-k) binary
        stderr: param passed to subprocess.run to control whether to capture stderr
        """
        self.exiftool_path = exiftool_path
        self.exiftoolk_path = exiftoolk_path
        self.stderr = stderr

        """
        Check the avaiablity of the exiftool binary
        Ensure that exiftoolk_path path to is the one that shoudl be used.
        """
        full_cmd1: T.List[str] = [self.exiftool_path, '-ver']
        LOG.debug(f"Check exiftool command presence #1: {' '.join(full_cmd1)}")
        try:
            subprocess.run(full_cmd1, check=True, stderr=self.stderr)
            LOG.info(f"The exiftool command OK: {self.exiftool_path}")
        except FileNotFoundError:
            self.exiftool_path = None
            LOG.info('The exiftoo1 command "{self.exiftoolk_path}" was not found.')
        except subprocess.CalledProcessError as ex:
            raise ExiftoolCalledProcessError(ex) from ex

        full_cmd2: T.List[str] = [self.exiftoolk_path, '-ver']
        LOG.debug(f"Verify exiftool command presence #2: {' '.join(full_cmd2)}")
        try:
            subprocess.run(full_cmd2, check=True, stderr=self.stderr)
            if self.exiftool_path is None:
                self.exiftool_path = self.exiftoolk_path
                self.exiftoolk_path = None
            LOG.info(f"The exiftool command OK: {self.exiftool_path}")
        except FileNotFoundError:
            self.exiftoolk_path = None
            LOG.debug('The exiftoo1 command "{self.exiftoolk_path}" was not found.')
        except subprocess.CalledProcessError as ex:
            raise ExiftoolCalledProcessError(ex) from ex

        if self.exiftool_path is None:
            raise ExiftoolNotFoundError(
                f'The exiftool command "{self.exiftool_path}" was not found'
            )
        LOG.debug(f"Check for exiftool done.")

    def _run_exiftool_write_gpx(self, cmd: T.List[str]) -> None:
        if not self.exiftool_path:
            LOG.warning(f"Skippig .gpx creation, no exiftool")
            return

        full_cmd: T.List[str] = [self.exiftool_path, *cmd]
        LOG.info(f"Creating .GPX file : {' '.join(full_cmd)}")
        try:
            subprocess.run(full_cmd, check=True, stderr=self.stderr)
        except FileNotFoundError:
            raise ExiftoolNotFoundError(
                f'The exiftool command "{self.exiftool_path}" not found'
            )
        except subprocess.CalledProcessError as ex:
            raise ExiftoolCalledProcessError(ex) from ex

    def _gpx_fmt_write(self) -> str:
        """ would be better to simply load the file from the bython sources somehow, but..."""
        fmt = tempfile.NamedTemporaryFile(prefix="gpx.fmt_",
                                          suffix=".tmp",
                                          delete=False)
        LOG.info(f"formatfile file is: '{fmt.name}'")
        gpx_fmt = '\n'.join([
            '#------------------------------------------------------------------------------',
            '# File:         gpx.fmt',
            '#',
            '# Description:  Example ExifTool print format file to generate a GPX track log',
            '#',
            '# Usage:        exiftool -p gpx.fmt -ee3 FILE [...] > out.gpx',
            '#',
            '# Requires:     ExifTool version 10.49 or later',
            '#',
            '# Revisions:    2010/02/05 - P. Harvey created',
            '#               2018/01/04 - PH Added IF to be sure position exists',
            '#               2018/01/06 - PH Use DateFmt function instead of -d option',
            '#               2019/10/24 - PH Preserve sub-seconds in GPSDateTime value',
            '#',
            '# Notes:     1) Input file(s) must contain GPSLatitude and GPSLongitude.',
            '#            2) The -ee3 option is to extract the full track from video files.',
            '#            3) The -fileOrder option may be used to control the order of the',
            '#               generated track points when processing multiple files.',
            '#            4) Coordinates are written at full resolution.  To change this,',
            '#               remove the "#" from the GPSLatitude/Longitude tag names below',
            '#               and use the -c option to set the desired precision.',
            '#------------------------------------------------------------------------------',
            '#[HEAD]<?xml version="1.0" encoding="utf-8"?>',
            '#[HEAD]<gpx version="1.0"',
            '#[HEAD] creator="ExifTool $ExifToolVersion"',
            '#[HEAD] xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            '#[HEAD] xmlns="http://www.topografix.com/GPX/1/0"',
            '#[HEAD] xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">',
            '#[HEAD]<trk>',
            '#[HEAD]<number>1</number>',
            '#[HEAD]<trkseg>',
            '#[IF]  $gpslatitude $gpslongitude',
            '#[BODY]<trkpt lat="$gpslatitude#" lon="$gpslongitude#">',
            '#[BODY]  <ele>$gpsaltitude#</ele>',
            '#[BODY]  <time>${gpsdatetime#;my ($ss)=/\.\d+/g;DateFmt("%Y-%m-%dT%H:%M:%SZ");s/Z/${ss}Z/ if $ss}</time>',
            '#[BODY]</trkpt>',
            '#[TAIL]</trkseg>',
            '#[TAIL]</trk>',
            '#[TAIL]</gpx>',
            '',])
        fmt.write(gpx_fmt.encode())
        fmt.close()
        LOG.debug(f"format is: \n{gpx_fmt}")
        self.gpx_fmt = fmt.name
        return self.gpx_fmt


# Cache command path
et = None

class exiftool:
    pass

def extract_camera_model(video_path: Path) -> str:
    LOG.info(f"C:extract_camera_model file : {video_path}")
    et = exiftool()
    return "GpxFromVideo0"

def extract_gpx(video_path: Path) -> str:
    LOG.info(f"Videofile as .gpx source : {video_path}")
    gpx_name = video_path.with_suffix('.gpx.tmp')
    gpx_path = Path(gpx_name)
    #if gpx_path.exsists():
    gpx_path.unlink(missing_ok=True) # Allow rerun.
    LOG.info(f"File to create gpx : {gpx_path}")
    et = EXIFTOOL()
    gpx_fmt = et._gpx_fmt_write()
    full_cmd: T.List[str] = ["cp", str(gpx_fmt), 'C:/cygwin64/tmp/gpx.fmt_6zfipdqu.fmt', ]
    try:
        subprocess.run(full_cmd, check=True)
    except subprocess.CalledProcessError as ex:
        raise ExiftoolCalledProcessError(ex) from ex
    cmd: T.List[str] = [
        "-p", str(gpx_fmt),
        "-api", 'largefilesupport=1',
        "-ee",
        #'-w', str(gpx_path),
        '-w', '%d/%f.gpx.tmp', # This will probaly fail if there is no dir in video_path
        str(video_path),
    ]
    et._run_exiftool_write_gpx(cmd)
    Path(gpx_fmt).unlink()
    return gpx_path

