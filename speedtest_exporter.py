#!/bin/env/python3
from __future__ import print_function
import subprocess
import json
import sys
import time
import random
import argparse
import logging
import os


from prometheus_client import Gauge, Summary, start_http_server

from logging import getLogger, StreamHandler, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def sleep_interval(t):
    logging.info('sleep: %ss', t)

    num = 0
    while (num < t):
        logging.debug('sleep: %ss', t)
        speedtest_cache_count.set(t)
        time.sleep(1)
        t -= 1


if __name__ == '__main__':

#- Argument parameter

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
        type=int,
        default=int(os.environ.get('EXPORTER_INTERVAL', '1200')),
        help="interval default second (default: 1200)",
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
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z',level=logging.INFO)
        logging.info('is when this event was logged.')
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z',level=logging.DEBUG)
        logging.debug('is when this event was logged.')


    # Start up the server to expose the metrics.
    start_http_server(args.port, args.listen)
    # Generate some requests.



    speedtest_download_bits = Gauge(
        'speedtest_download_bits',
        'download bandwidth in (bit/s)',
        [
            'ip', 'client_isp', 'client_country',
            'server_name', 'server_id', 'server_country', 'server_sponsor'
        ]
    )

    speedtest_upload_bits = Gauge(
        'speedtest_upload_bits',
        'upload bandwidth in (bit/s)',
        [
            'ip', 'client_isp', 'client_country',
            'server_name', 'server_id', 'server_country', 'server_sponsor'
        ]
    )

    speedtest_download_bytes = Gauge(
        'speedtest_download_bytes',
        'download usage capacity (bytes)',
        [
            'ip', 'client_isp', 'client_country',
            'server_name', 'server_id', 'server_country', 'server_sponsor'
        ]
    )

    speedtest_upload_bytes = Gauge(
        'speedtest_upload_bytes',
        'upload usage capacity (bytes)',
        [
            'ip', 'client_isp', 'client_country',
            'server_name', 'server_id', 'server_country', 'server_sponsor'
        ]
    )

    speedtest_ping = Gauge(
        'speedtest_ping',
        'icmp latency (ms)',
        [
            'ip', 'client_isp', 'client_country',
            'server_name', 'server_id', 'server_country', 'server_sponsor'
        ]
    )

    speedtest_cache_interval = Gauge(
        'speedtest_cache_interval',
        'cache interval')

    speedtest_cache_count = Gauge(
        'speedtest_cache_count',
        'cache count down')

    speedtest_up = Gauge(
        'speedtest_up',
        'speedtest_exporter is up(1) or down(0)')



def main():
    while True:
        try:
            logging.info('Running speedtest-cli subprocess.')

            if args.server == '':
                s1 = subprocess.Popen(['speedtest-cli', '--json'], stdout=subprocess.PIPE, universal_newlines=True)
            else:
                logging.info('set server id: %s', args.server)
                s1 = subprocess.Popen(['speedtest-cli', '--json', '--server', args.server], stdout=subprocess.PIPE, universal_newlines=True)

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
                        'ip':'unknown',
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


        speedtest_download_bits.labels(
            st_json['client']['ip'], st_json['client']['isp'], st_json['client']['country'],
            st_json['server']['name'], st_json['server']['id'], st_json['server']['cc'], st_json['server']['sponsor']
        ).inc(st_json['download'])

        speedtest_upload_bits.labels(
            st_json['client']['ip'], st_json['client']['isp'], st_json['client']['country'],
            st_json['server']['name'], st_json['server']['id'], st_json['server']['cc'], st_json['server']['sponsor']
        ).inc(st_json['upload'])

        speedtest_download_bytes.labels(
            st_json['client']['ip'], st_json['client']['isp'], st_json['client']['country'],
            st_json['server']['name'], st_json['server']['id'], st_json['server']['cc'], st_json['server']['sponsor']
        ).inc(st_json['bytes_received'])

        speedtest_upload_bytes.labels(
            st_json['client']['ip'], st_json['client']['isp'], st_json['client']['country'],
            st_json['server']['name'], st_json['server']['id'], st_json['server']['cc'], st_json['server']['sponsor']
        ).inc(st_json['bytes_sent'])

        speedtest_ping.labels(
            st_json['client']['ip'], st_json['client']['isp'], st_json['client']['country'],
            st_json['server']['name'], st_json['server']['id'], st_json['server']['cc'], st_json['server']['sponsor']
        ).inc(st_json['ping'])


        speedtest_cache_interval.set(args.interval)
        sleep_interval(args.interval)

if __name__ == "__main__":
    main()
