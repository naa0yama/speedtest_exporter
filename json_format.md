
```json
{
  "bytes_sent": 5242880,
  "download": 5649262.632440399,
  "timestamp": "2018-07-27T13:14:21.782347Z",
  "share": null,
  "bytes_received": 7203980,
  "ping": 45.007,
  "upload": 3279752.8049338055,
  "client": {
    "rating": "0",
    "loggedin": "0",
    "isprating": "3.7",
    "ispdlavg": "0",
    "ip": "126.225.90.142",
    "isp": "Softbank BB",
    "lon": "139.7514",
    "ispulavg": "0",
    "country": "JP",
    "lat": "35.685"
  },
  "server": {
    "latency": 45.007,
    "name": "Bunkyo",
    "url": "http://speed.coe.ad.jp/upload.php",
    "country": "Japan",
    "lon": "139.7522",
    "cc": "JP",
    "host": "speed.coe.ad.jp:8080",
    "sponsor": "IPA CyberLab",
    "lat": "35.7081",
    "id": "14623",
    "d": 2.569618530339375
  }
}

```

|                    |                                                     |         |
| :----------------- | :-------------------------------------------------- | :------ |
| `bytes_sent`       | upload size                                         | bytes   |
| `download`         | download bandwidth in bytes per second                      | bit/s |
| `timestamp`        | timestamp                                           | ISO8601 |
| `share`            | share url                                           |
| `bytes_received`   | Download size                                       | bytes   |
| `ping`             | icmp latency                                        | ms      |
| `upload`           | Upload bandwidth in bytes per second                        | bit/s |
|                    |
| `client`           | JSON Object                                         |
| `client.rating`    | another rating, which is always 0 it seems          |
| `client.loggedin`  | ?                                                   |
| `client.isprating` | some kind of rating                                 |
| `client.ispdlavg`  | avg download speed by all users of this isp in Mbps |
| `client.ip`        | ip of client                                        |
| `client.isp`       | ISP(Internet Service Provider) name                 |
| `client.lat`       | latitude of client                                  |
| `client.lon`       | longitude of client                                 |
| `client.ispulavg`  | same for upload                                     |
| `client.country`   | Country Code                                        |
|                    |
| `server`           | JSON Object                                         |
| `server.latency`   | server latency                                      |
| `server.name`      | server name                                         |
| `server.url`       | server test url                                     |
| `server.country`   | Country name                                        |
| `server.lat`       | latitude of client                                  |
| `server.lon`       | longitude of client                                 |
| `server.cc`        | country code                                        |
| `server.host`      | server host name                                    |
| `server.sponsor`   | sponsor name                                        |
| `server.id`        | server id                                           |
| `server.d`         | ?                                                   |


## Prometheus

prefix: speedtest

* speedtest_download_bits
  * `download`

* speedtest_upload_bits
  * `upload`


* speedtest_download_bytes
  * `bytes_received`

* speedtest_upload_bytes
  * `bytes_sent`

* speedtest_ping
  * `ping`

* speedtest_cache_count
* speedtest_cache_interval
* speedtest_up
  *

## Labels

* client.ip
* client.isp
* client.country

* server.id
* server.name
* server.cc
* server.sponsor

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
