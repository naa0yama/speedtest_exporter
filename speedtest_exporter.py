#!/bin/env/python3

from __future__ import print_function
import subprocess
import json
import sys
import time
import argparse
import logging
import os
import math


from crontab import CronTab
from datetime import datetime, timedelta
from prometheus_client import Gauge, start_http_server
from logging import getLogger, StreamHandler, DEBUG
from multiprocessing import Pool


logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class JobConfig(object):
    """
    処理設定
    """

    def __init__(self, crontab):
        """
        :type crontab: crontab.CronTab
        :param crontab: 実行時間設定
        """

        self._crontab = crontab

    def schedule(self):
        """
        次回実行日時を取得する。
        :rtype: datetime.datetime
        :return: 次回実行日時を
        """

        crontab = self._crontab
        return datetime.now() + timedelta(
            seconds=math.ceil(
                crontab.next(default_utc=False)
            )
        )

    def next(self):
        """
        次回実行時刻まで待機する時間を取得する。
        :rtype: long
        :retuen: 待機時間(秒)
        """

        crontab = self._crontab
        return math.ceil(crontab.next(default_utc=False))


def job_controller(crontab):
    """
    処理コントローラ
    :type crontab: str
    :param crontab: 実行設定
    """
    def receive_func(job):
        import functools
        @functools.wraps(job)

        def wrapper():
            # Start up the server to expose the metrics.
            start_http_server(args.port, args.listen)
            # Generate some requests.
            jobConfig = JobConfig(CronTab(crontab))
            logging.info("->- Process Start")
            while True:
                try:
                    # 次実行日時を表示
                    logging.info("-?- next running\tschedule:%s" %
                    jobConfig.schedule().strftime("%Y-%m-%d %H:%M:%S"))
                    # 次実行時刻まで待機
                    time.sleep(jobConfig.next())

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
    default=os.environ.get('EXPORTER_LISTEN', '0.0.0.0'),
    help="listen port number. (default: 0.0.0.0)",
)

parser.add_argument(
    "-p",
    "--port",
    type=int,
    default=int(os.environ.get('EXPORTER_PORT', '9353')),
    help="listen port number. (default: 9353)",
)

parser.add_argument(
    "-i",
    "--interval",
    type=str,
    default=os.environ.get('EXPORTER_INTERVAL', '*/20 * * * *'),
    help="interval default second (default: */20 * * * *)",
)

parser.add_argument(
    "-v",
    "--debug",
    default=os.environ.get('EXPORTER_DEBUG', 'false'),
    help="log level. (default: False)",
    action="store_true"
)

parser.add_argument(
    "-s",
    "--server",
    type=str,
    default=os.environ.get('EXPORTER_SERVERID', ''),
    help="speedtest server id"
)

args = parser.parse_args()


if args.debug == 'false':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z',
        level=logging.INFO
    )
    logging.info('is when this event was logged.')
else:
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z',
        level=logging.DEBUG
    )
    logging.debug('is when this event was logged.')


speedtest_download_bits = Gauge(
    'speedtest_download_bits',
    'download bandwidth in (bit/s)'
)

speedtest_upload_bits = Gauge(
    'speedtest_upload_bits',
    'upload bandwidth in (bit/s)'
)

speedtest_download_bytes = Gauge(
    'speedtest_download_bytes',
    'download usage capacity (bytes)'
)

speedtest_upload_bytes = Gauge(
    'speedtest_upload_bytes',
    'upload usage capacity (bytes)'
)

speedtest_ping = Gauge(
    'speedtest_ping',
    'icmp latency (ms)'
)

speedtest_up = Gauge(
    'speedtest_up',
    'speedtest_exporter is up(1) or down(0)'
)




@job_controller(args.interval)
def job1():
    """
    処理1
    """
    try:
        logging.info('Running speedtest-cli subprocess.')

        if args.server == '':
            s1 = subprocess.Popen([
                'speedtest-cli', '--json'],
                stdout=subprocess.PIPE,
                universal_newlines=True
            )
        else:
            logging.info('set server id: %s', args.server)
            s1 = subprocess.Popen(
                ['speedtest-cli', '--json', '--server', args.server],
                stdout=subprocess.PIPE,
                universal_newlines=True
            )

        logging.info('Communicating with subprocess.')
        s2 = s1.communicate()
        try:
            logging.info('Loading speedtest into JSON variable.')
            st_json = json.loads(s2[0])
            speedtest_up.set(1)

        except json.decoder.JSONDecodeError:
            logging.warning('ERROR: Failed to parse JSON, setting all values to 0')
            logging.warning("ERROR: Failed to parse JSON, setting all values to 0!")
            st_json = {
                'download': 0,
                'upload': 0,
                'ping': 0,
                'bytes_received': 0,
                'bytes_sent': 0,
                'client': {
                    'ip': 'unknown',
                    'isp': 'unknown',
                    'country': 'unknown'
                },
                'server': {
                    'name': 'unknown',
                    'id': 0,
                    'cc': 'unknown',
                    'sponsor': 'unknown'
                }
            }

            speedtest_up.set(0)

    except TypeError:
        logging.warning("Couldn't get results from speedtest-cli!")

    logging.info('Setting gauge values.')

    speedtest_download_bits.set(st_json['download'])
    speedtest_upload_bits.set(st_json['upload'])
    speedtest_download_bytes.set(st_json['bytes_received'])
    speedtest_upload_bytes.set(st_json['bytes_sent'])
    speedtest_ping.set(st_json['ping'])


def main():
    """
    """

    # ログ設定
    logging.basicConfig(
        level=logging.DEBUG,
        format="time:%(asctime)s.%(msecs)03d\tprocess:%(process)d"
        + "\tmessage:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 処理リスト作成
    jobs = [job1]

    # 処理を並列に実行
    p = Pool(len(jobs))
    try:
        for job in jobs:
            p.apply_async(job)
        p.close()
        p.join()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
