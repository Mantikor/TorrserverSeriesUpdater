[![Docker Image](https://github.com/Mantikor/TorrserverSeriesUpdater/actions/workflows/docker-image.yml/badge.svg)](https://github.com/Mantikor/TorrserverSeriesUpdater/actions/workflows/docker-image.yml)

# Updater for torrents with new episodes of series on TorrServer from Litr.cc or Rutor

## Installation

### Docker container

```
sudo docker pull mantik0r/torrserver_series_updater:latest
```

### Python script

## Running

### Docker container

```
sudo docker run --rm torrserver_series_updater:latest python series_updater.py --litrcc RSS_FEED_UUID --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```

**RSS_FEED_UUID**, like as 21100112-ffff-aaaa-cccc-e00110011fff - Litr.cc RSS feed identifier

**TORRSERVER_URL**, like as http://192.168.1.2 - ip address of TorrServer instance (if not set, will be default: _http://127.0.0.1_)

**TORRSERVER_PORT**, like as 8090 - port of TorrServer instance (if not set, default: _8090_)

### Python script

#### Run update from Litr.cc without settings file

`series_updater.py --litrcc 21100112-ffff-aaaa-cccc-e00110011fff --ts_url http://192.168.1.2`

#### Run update from Rutor without settings file

`series_updater.py --rutor --ts_url http://192.168.1.2`

### log sample
```
2023-02-12 23:58:43,466 INFO [load_config] - Settings loaded from file: config.yaml
2023-02-12 23:58:43,536 INFO [_raw2struct] - Torrserver, torrents got: 53
2023-02-12 23:58:43,773 INFO [_raw2struct] - Litr.cc mode: torrents got: 5
2023-02-12 23:58:43,773 INFO [main] - Litr.cc mode: RSS uuid: 20000000-ffff-ffff-ffff-200000000000
2023-02-12 23:58:44,041 INFO [main] - Территория [02х01-05 из 08] (2022) WEBRip 1080p => added/updated
2023-02-12 23:58:44,229 INFO [main] - 1 episode => set as viewed
2023-02-12 23:58:44,251 INFO [main] - 2 episode => set as viewed
2023-02-12 23:58:44,275 INFO [main] - 3 episode => set as viewed
2023-02-12 23:58:44,317 INFO [main] - Old torrent with hash: f3215ad290fa443a57ae22fabd42debb22342d56 => deleted successfully
2023-02-12 23:58:44,354 INFO [main] - Old torrent with hash: 7d9abeda29e8a96567716283292193c26c304328 => deleted successfully
2023-02-12 23:58:44,369 INFO [main] - Old torrent with hash: e06823f26091d9cc988d0558e6f6a82c9e505322 => deleted successfully
```

[TorrServer](https://github.com/YouROK/TorrServer) by YouROK

[TorrServer Adder for Chrome](https://chrome.google.com/webstore/detail/torrserver-adder/ihphookhabmjbgccflngglmidjloeefg)

[TorrServer Adder for Firefox](https://addons.mozilla.org/ru/firefox/addon/torrserver-adder/)

[TorrServe client on 4PDA](https://4pda.to/forum/index.php?showtopic=889960)