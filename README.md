# Prometheus Speedtest Exporter

Exposes Speedtest metrics to Prometheus.

## Configuration

This exporter is configurable via environment variables:


### Optional

* `EXPORTER_LISTEN` The listen to be used by the exporter. Default `0.0.0.0`.
* `EXPORTER_PORT` The port to be used by the exporter. Default `9353`.
* `EXPORTER_INTERVAL` Speedtest execution interval
* `EXPORTER_DEBUG` Debug mode. Default `false`
* `EXPORTER_SERVERID` Specify a server ID to test against.


## Metrics

The following is a sample metrics you can get from this exporter:

```conf
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="6",patchlevel="0",version="3.6.0"} 1.0
# HELP speedtest_download_bits download bandwidth in (bit/s)
# TYPE speedtest_download_bits gauge
speedtest_download_bits{client_country="JP",client_isp="Softbank BB",instance="126.225.90.142",server_country="JP",server_id="14623",server_name="Bunkyo",server_sponsor="IPA CyberLab"} 5649262.632440399
# HELP speedtest_upload_bits upload bandwidth in (bit/s)
# TYPE speedtest_upload_bits gauge
speedtest_upload_bits{client_country="JP",client_isp="Softbank BB",instance="126.225.90.142",server_country="JP",server_id="14623",server_name="Bunkyo",server_sponsor="IPA CyberLab"} 3279752.8049338055
# HELP speedtest_download_bytes download usage capacity (bytes)
# TYPE speedtest_download_bytes gauge
speedtest_download_bytes{client_country="JP",client_isp="Softbank BB",instance="126.225.90.142",server_country="JP",server_id="14623",server_name="Bunkyo",server_sponsor="IPA CyberLab"} 7203980.0
# HELP speedtest_upload_bytes upload usage capacity (bytes)
# TYPE speedtest_upload_bytes gauge
speedtest_upload_bytes{client_country="JP",client_isp="Softbank BB",instance="126.225.90.142",server_country="JP",server_id="14623",server_name="Bunkyo",server_sponsor="IPA CyberLab"} 5242880.0
# HELP speedtest_ping icmp latency (ms)
# TYPE speedtest_ping gauge
speedtest_ping{client_country="JP",client_isp="Softbank BB",instance="126.225.90.142",server_country="JP",server_id="14623",server_name="Bunkyo",server_sponsor="IPA CyberLab"} 45.007
# HELP speedtest_cache_interval cache interval
# TYPE speedtest_cache_interval gauge
speedtest_cache_interval 1200.0
# HELP speedtest_cache_count cache count down
# TYPE speedtest_cache_count gauge
speedtest_cache_count 1197.0
# HELP speedtest_up speedtest_exporter is up(1) or down(0)
# TYPE speedtest_up gauge
speedtest_up 1.0

```

## Usage

There's a sample `docker-compose.yml` to be used to test this exporter with prometheus and grafana. Hit the command below:

```bash
docker-compose up

```

## Grafana

The following is what it would look like with integration with Grafana:

![Grafana](assets/grafana.png)
