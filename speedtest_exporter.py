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
import random


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
    u"""
    処理設定
    """

    def __init__(self, crontab):
        u"""
        :type crontab: crontab.CronTab
        :param crontab: 実行時間設定
        """
        self._crontab = crontab

    def schedule(self):
        u"""
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
        u"""
        次回実行時刻まで待機する時間を取得する。
        :rtype: long
        :retuen: 待機時間(秒)
        """
        crontab = self._crontab
        return math.ceil(crontab.next(default_utc=False))


def job_controller(crontab):
    u"""
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
                    strargs = jobConfig.schedule().strftime("%Y-%m-%d %H:%M:%S")
                    logging.info("-?- next running\tschedule:%s" % strargs)
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

logging.info('Using parser args = %r' % (args, ))

speedtest_download_bits = Gauge(
    'speedtest_download_bits',
    'download bandwidth in (bit/s)',
    ['serverid'],
)

speedtest_upload_bits = Gauge(
    'speedtest_upload_bits',
    'upload bandwidth in (bit/s)',
    ['serverid'],
)

speedtest_download_bytes = Gauge(
    'speedtest_download_bytes',
    'download usage capacity (bytes)',
    ['serverid'],
)

speedtest_upload_bytes = Gauge(
    'speedtest_upload_bytes',
    'upload usage capacity (bytes)',
    ['serverid'],
)

speedtest_ping = Gauge(
    'speedtest_ping',
    'icmp latency (ms)',
    ['serverid'],
)

speedtest_up = Gauge(
    'speedtest_up',
    'speedtest_exporter is up(1) or down(0)',
)

logging.info('Getting closest 10 servers (by distance)')
server_list = []
try:
    logging.info('Running speedtest-cli subprocess.')

    s1 = subprocess.Popen([
        'speedtest-cli', '--list'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    s2 = s1.communicate()
    try:
        lines = s2[0].strip().split('\n')
        for line in lines:
            try:
                line = line.strip().split()
                serverid = line[0]
                distance = line[-2]
                serverid = serverid.strip(')').strip()
                distance = distance.strip('[').strip()
                serverid = int(serverid)
                distance = float(distance)
                valid = True
            except:
                valid = False
            if valid:
                server = (distance, serverid, )
                server_list.append(server)
        server_list = sorted(server_list)
        server_list = server_list[:10]
        logging.info('Using server list: %r' % (server_list, ))
    except:
        pass
except:
    logging.warning("Couldn't get results from speedtest-cli!")


@job_controller(args.interval)
def job1():
    u"""
    処理1
    """
    try:
        logging.info('Running speedtest-cli subprocess.')

        serverid = str(args.server)

        if serverid == 'random':
            if len(server_list) == 0:
                serverid = ''
            else:
                random.shuffle(server_list)
                server = server_list[0]
                serverid = str(server[1])
                logging.info('Selected random server = %r' % (server, ))

        logging.info('Requesting serverid = %r' % (serverid, ))
        if serverid == '':
            s1 = subprocess.Popen([
                'speedtest-cli', '--json'],
                stdout=subprocess.PIPE,
                universal_newlines=True
            )
        else:
            logging.info('set server id: %s', serverid)
            s1 = subprocess.Popen(
                ['speedtest-cli', '--json', '--server', serverid],
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

    except:
        logging.warning("Couldn't get results from speedtest-cli!")

    logging.info('Setting gauge values.')
    handler.flush()

    serverid = str(st_json['server']['id'])
    logging.info('Used serverid = %r' % (serverid, ))

    speedtest_download_bits.labels(serverid=serverid).set(st_json['download'])
    speedtest_upload_bits.labels(serverid=serverid).set(st_json['upload'])
    speedtest_download_bytes.labels(serverid=serverid).set(st_json['bytes_received'])
    speedtest_upload_bytes.labels(serverid=serverid).set(st_json['bytes_sent'])
    speedtest_ping.labels(serverid=serverid).set(st_json['ping'])


def main():
    """
    """
    # ログ設定
    logging.basicConfig(
        level=logging.DEBUG,
        format="time:%(asctime)s.%(msecs)03d\tprocess:%(process)d" + "\tmessage:%(message)s",
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
    handler.flush()


if __name__ == "__main__":
    main()
