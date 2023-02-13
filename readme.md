Copyright: (c) 2023, Streltsov Sergey, straltsou.siarhei@gmail.com
init release 2023-02-10

The program for updating torrents with new episodes for series on torrserver from litr.cc

run:
series_updater.py --litrcc _feed_uuid_ --ts_url _http://192.168.1.2_ --settings config.yaml

log:
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
