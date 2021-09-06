#!/usr/bin/env python3
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
"""expoter."""

import argparse
from datetime import datetime
from datetime import timedelta
import json
import logging
from logging import DEBUG
from logging import StreamHandler
from logging import getLogger
import math
from multiprocessing import Pool
import os
import subprocess
import time
from typing import Any

from crontab import CronTab
from prometheus_client import Gauge
from prometheus_client import start_http_server

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


class JobConfig:
    """Processing settings."""

    def __init__(self: CronTab, crontab: CronTab) -> None:
        """Init.

        :type crontab: crontab.CronTab
        :param crontab: 実行時間設定
        """
        self._crontab = crontab

    def schedule(self: CronTab) -> datetime:
        """Get the next execution date and time.

        Returns:
            [type]: Next execution date and time
        """
        crontab = self._crontab
        return datetime.now() + timedelta(
            seconds=math.ceil(crontab.next(default_utc=False)),  # noqa: B305
        )

    def next_sec(self: CronTab) -> int:
        """Get the time to wait until the next execution time.

        Returns:
            [int]: Wait time (seconds).
        """
        crontab = self._crontab
        return math.ceil(crontab.next(default_utc=False))  # noqa: B305


def job_controller(crontab: str) -> Any:
    """Processing controller."""

    def receive_func(job: Any) -> Any:
        """receive_func."""
        import functools

        @functools.wraps(job)
        def wrapper() -> Any:
            """Start up the server to expose the metrics."""
            start_http_server(args.port, args.listen)
            # Generate some requests.
            jobConfig = JobConfig(CronTab(crontab))
            logging.info("->- Process Start")
            while True:
                try:
                    # 次実行日時を表示
                    logging.info(
                        "-?- next running\tschedule:%s"
                        % jobConfig.schedule().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    # 次実行時刻まで待機
                    time.sleep(jobConfig.next_sec())

                    logging.info("-!> Job Start")

                    # 処理を実行する。
                    job()

                    logging.info("-!< Job Done")

                except KeyboardInterrupt:
                    break

        logging.info("-<- Process Done.")
        return wrapper

    return receive_func


# Argument parameter
parser = argparse.ArgumentParser()

parser.add_argument(
    "-l",
    "--listen",
    type=str,
    default=os.environ.get("EXPORTER_LISTEN", "0.0.0.0"),
    help="listen port number. (default: 0.0.0.0)",
)

parser.add_argument(
    "-p",
    "--port",
    type=int,
    default=int(os.environ.get("EXPORTER_PORT", "9353")),
    help="listen port number. (default: 9353)",
)

parser.add_argument(
    "-i",
    "--interval",
    type=str,
    default=os.environ.get("EXPORTER_INTERVAL", "*/20 * * * *"),
    help="interval default second (default: */20 * * * *)",
)

parser.add_argument(
    "-v",
    "--debug",
    default=os.environ.get("EXPORTER_DEBUG", "true"),
    help="log level. (default: False)",
    action="store_true",
)

parser.add_argument(
    "-s",
    "--server",
    type=str,
    default=os.environ.get("EXPORTER_SERVERID", "24333"),
    help="speedtest server id",
)

args = parser.parse_args()


if args.debug == "false":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=logging.INFO,
    )
    logging.info("is when this event was logged.")
else:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=logging.DEBUG,
    )
    logging.debug("is when this event was logged.")


speedtest_download_bits_per_second = Gauge(
    "speedtest_download_bits_per_second",
    "Speedtest current Download Speed in bit/s",
    [
        "isp",
        "server_id",
        "server_name",
        "server_location",
        "server_country",
    ],
)

speedtest_upload_bits_per_second = Gauge(
    "speedtest_upload_bits_per_second",
    "Speedtest current Upload speed in bits/s",
    [
        "isp",
        "server_id",
        "server_name",
        "server_location",
        "server_country",
    ],
)

speedtest_jitter_latency_milliseconds = Gauge(
    "speedtest_jitter_latency_milliseconds",
    "Speedtest current Jitter in ms",
    [
        "isp",
        "server_id",
        "server_name",
        "server_location",
        "server_country",
    ],
)

speedtest_ping_latency_milliseconds = Gauge(
    "speedtest_ping_latency_milliseconds",
    "Speedtest current Ping in ms",
    [
        "isp",
        "server_id",
        "server_name",
        "server_location",
        "server_country",
    ],
)

speedtest_up = Gauge("speedtest_up", "speedtest_exporter is up(1) or down(0)")


def bytes_to_bits(bytes_per_sec: int) -> int:
    """Bytes to bits.

    Args:
        bytes_per_sec (int): result bandwidth.

    Returns:
        int: bits/s.
    """
    return bytes_per_sec * 8


@job_controller(args.interval)
def job1() -> None:
    """Process 1."""
    try:
        logging.info("Running speedtest-cli subprocess.")

        if args.server == "":
            s1 = subprocess.Popen(
                ["speedtest", "--accept-license", "--servers"],
                stdout=subprocess.PIPE,
                universal_newlines=True,
            )
        else:
            logging.info("set server id: %s", args.server)
            s1 = subprocess.Popen(
                [
                    "speedtest",
                    "--accept-license",
                    "--progress=no",
                    "--format=json",
                    "--server-id",
                    args.server,
                ],
                stdout=subprocess.PIPE,
                universal_newlines=True,
            )

        logging.info("Communicating with subprocess.")
        s2 = s1.communicate()
        try:
            logging.info("Loading speedtest into JSON variable.")
            st_json = json.loads(s2[0])
            speedtest_up.set(1)

        except json.decoder.JSONDecodeError:
            logging.warning("ERROR: Failed to parse JSON, setting all values to 0")
            logging.warning("ERROR: Failed to parse JSON, setting all values to 0!")
            st_json = {
                "ping": {
                    "jitter": 0,
                    "latency": 0,
                },
                "download": {
                    "bandwidth": 0,
                    "bytes": 0,
                    "elapsed": 0,
                },
                "upload": {"bandwidth": 0, "bytes": 0, "elapsed": 0},
                "packetLoss": 0,
                "isp": "Unknown",
                "interface": {
                    "internalIp": "Unknown",
                    "name": "Unknown",
                    "macAddr": "Unknown",
                    "isVpn": "false",
                    "externalIp": "Unknown",
                },
                "server": {
                    "id": 0,
                    "name": "Unknown",
                    "location": "Unknown",
                    "country": "Unknown",
                    "host": "Unknown",
                    "port": 0,
                    "ip": "Unknown",
                },
            }

            speedtest_up.set(0)

    except TypeError:
        logging.warning("Couldn't get results from speedtest !")

    logging.info("Setting gauge values.")

    speedtest_download_bits_per_second.labels(
        st_json["isp"],
        st_json["server"]["id"],
        st_json["server"]["name"],
        st_json["server"]["location"],
        st_json["server"]["country"],
    ).set(bytes_to_bits(st_json["download"]["bandwidth"]))

    speedtest_upload_bits_per_second.labels(
        st_json["isp"],
        st_json["server"]["id"],
        st_json["server"]["name"],
        st_json["server"]["location"],
        st_json["server"]["country"],
    ).set(bytes_to_bits(st_json["upload"]["bandwidth"]))

    speedtest_jitter_latency_milliseconds.labels(
        st_json["isp"],
        st_json["server"]["id"],
        st_json["server"]["name"],
        st_json["server"]["location"],
        st_json["server"]["country"],
    ).set(st_json["ping"]["jitter"])

    speedtest_ping_latency_milliseconds.labels(
        st_json["isp"],
        st_json["server"]["id"],
        st_json["server"]["name"],
        st_json["server"]["location"],
        st_json["server"]["country"],
    ).set(st_json["ping"]["latency"])


def main() -> None:
    """Main."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="time:%(asctime)s.%(msecs)03d\tprocess:%(process)d" + "\tmessage:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 処理リスト作成
    jobs = [job1]

    # 処理を並列に実行
    proc = Pool(len(jobs))
    try:
        for job in jobs:
            proc.apply_async(job)
        proc.close()
        proc.join()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
