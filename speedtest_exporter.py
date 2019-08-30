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

            MIN_AVG_PING = 1000
            server_rank = {}
            valid_server_list = []
            server_st_archive = {}
            olympics_serverid_list = []

            while True:
                try:
                    # 次実行日時を表示
                    strargs = jobConfig.schedule().strftime("%Y-%m-%d %H:%M:%S")
                    logging.info("-?- next running\tschedule:%s" % strargs)
                    # 次実行時刻まで待機
                    time.sleep(jobConfig.next())

                    logging.info("-!> Job Start")

                    if len(server_rank.keys()) < len(candidate_server_list):
                        server_list_ = []
                        for server in candidate_server_list:
                            serverid = server[1]
                            server_ping_list = server_rank.get(serverid, [])
                            strargs = (serverid, server_ping_list, )
                            if len(server_ping_list) < 3:
                                print('serverid = %r needs to be bootstrapped (pings = %r)' % strargs)
                                server_list_.append(server)
                            else:
                                print('serverid = %r is bootstrapped (pings = %r)' % strargs)
                        print('Bootstrapping with server_list_ = %r' % (server_list_, ))
                    elif len(valid_server_list) > 0 and random.uniform(0.0, 0.1):
                        server_list_ = valid_server_list
                        print('Random selection (p=0.1) with server_list_ = %r' % (server_list_, ))
                    else:
                        print('Ranking with server_rank = %r' % (server_rank, ))
                        print('Picking 5 best servers from candidates with lowest average ping')
                        valid_ping_list = []
                        for serverid in server_rank:
                            server_ping_list = server_rank.get(serverid, [])
                            while len(server_ping_list) < 3:
                                server_ping_list.append(0)
                            server_ping_list = server_ping_list[-3:]
                            avg_ping = sum(server_ping_list) / len(server_ping_list)
                            if avg_ping <= MIN_AVG_PING:
                                valid_ping_list.append((avg_ping, serverid))
                            server_rank[serverid] = server_ping_list

                        valid_ping_list = sorted(valid_ping_list)
                        print('valid_ping_list = %r' % (valid_ping_list, ))
                        valid_serverid_list = [value[1] for value in valid_ping_list]
                        num = min(len(valid_serverid_list), 5)
                        fastest_serverid_list = valid_serverid_list[:num]
                        print('fastest_serverid_list = %r' % (fastest_serverid_list, ))

                        if len(fastest_serverid_list) == 5:
                            # Exclude fastest and slowest from top 5 pings
                            olympics_serverid_list = fastest_serverid_list[1:-1]
                        else:
                            olympics_serverid_list = []
                        print('Updated olympics_serverid_list = %r' % (olympics_serverid_list, ))

                        valid_server_list = []
                        server_list_ = []
                        for server in candidate_server_list:
                            serverid = server[1]
                            if serverid in valid_serverid_list:
                                valid_server_list.append(server)
                            if serverid in fastest_serverid_list:
                                server_list_.append(server)
                        print('Updated valid_server_list = %r' % (valid_server_list, ))
                        print('Ranked selection with server_list_ = %r' % (server_list_, ))

                    # 処理を実行する。
                    server_list = server_list_[:]
                    # print('Sending server_list = %r' % (server_list, ))
                    serverid, st_json = job(server_list)

                    # Update rank
                    try:
                        ping = st_json['ping']
                        ping = float(ping)
                        if serverid not in server_rank:
                            server_rank[serverid] = []
                        server_rank[serverid].append(ping)
                        print('Updated server_rank[%s] = %r' % (serverid, server_rank[serverid], ))

                        # overwrite latest version
                        server_st_archive[serverid] = st_json
                        print('Updated server_st_archive[%s]' % (serverid, ))
                    except:
                        pass

                    key_list = ['download', 'upload', 'bytes_received', 'bytes_sent', 'ping']
                    st_json = {key: [] for key in key_list}
                    print('Using olympics_serverid_list = %r' % (olympics_serverid_list, ))
                    for olympics_serverid in olympics_serverid_list:
                        st_json_ = server_st_archive[olympics_serverid]
                        for key in key_list:
                            st_json[key].append(st_json_[key])

                    for key in key_list:
                        value_list = st_json[key]
                        while len(value_list) < 3:
                            value_list.append(0)
                        st_json[key] = sum(value_list) / len(value_list)

                    print('Updated olympics info = %r' % (st_json, ))
                    speedtest_download_bits.labels(serverid='olympics').set(st_json['download'])
                    speedtest_upload_bits.labels(serverid='olympics').set(st_json['upload'])
                    speedtest_download_bytes.labels(serverid='olympics').set(st_json['bytes_received'])
                    speedtest_upload_bytes.labels(serverid='olympics').set(st_json['bytes_sent'])
                    speedtest_ping.labels(serverid='olympics').set(st_json['ping'])

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
candidate_server_list = []
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
                serverid = str(int(serverid))
                distance = float(distance)
                valid = True
            except:
                valid = False
            if valid:
                server = (distance, serverid, )
                candidate_server_list.append(server)
        candidate_server_list = sorted(candidate_server_list)
        candidate_server_list = candidate_server_list[:10]
        logging.info('Using candidate server list: %r' % (candidate_server_list, ))
    except:
        pass
except:
    logging.warning("Couldn't get results from speedtest-cli!")


@job_controller(args.interval)
def job1(server_list):
    u"""
    処理1
    """
    try:
        logging.info('Running speedtest-cli subprocess.')

        serverid = str(args.server)

        if serverid == 'random':
            # print('Received server_list = %r' % (server_list, ))
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

    for serverid_ in ['*', serverid]:
        speedtest_download_bits.labels(serverid=serverid_).set(st_json['download'])
        speedtest_upload_bits.labels(serverid=serverid_).set(st_json['upload'])
        speedtest_download_bytes.labels(serverid=serverid_).set(st_json['bytes_received'])
        speedtest_upload_bytes.labels(serverid=serverid_).set(st_json['bytes_sent'])
        speedtest_ping.labels(serverid=serverid_).set(st_json['ping'])

    return serverid, st_json


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
