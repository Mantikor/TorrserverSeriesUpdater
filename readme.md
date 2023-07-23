[![Docker Image release](https://github.com/Mantikor/TorrserverSeriesUpdater/actions/workflows/docker-image-release.yml/badge.svg)](https://github.com/Mantikor/TorrserverSeriesUpdater/actions/workflows/docker-image-release.yml) [![Build binaries](https://github.com/Mantikor/TorrserverSeriesUpdater/actions/workflows/build-binaries.yml/badge.svg)](https://github.com/Mantikor/TorrserverSeriesUpdater/actions/workflows/build-binaries.yml) [![Github All Releases](https://img.shields.io/github/downloads/Mantikor/TorrserverSeriesUpdater/total.svg)]()

# Updater for torrents with new episodes of series on TorrServer, added from litr.cc (RSS-feed, supported all trackers) and added via TorrServer Adder: rutor.info(is), nnmclub.to, torrent.by, kinozal.tv, rutracker.org.

# Программа для обновления торрентов с сериалами в TorrServer. Обновляет раздачи с сериалами, которые обновляются путем добавления новых серий. Поддерживаются litr.cc (через чтение RSS-ленты, поддерживаются все трэкеры) и раздачи, добавленные через TorrServer Adder с трэкеров rutor.info(is), nnmclub.to, torrent.by, kinozal.tv, rutracker.org.

![](torrserver_updater.png)

## Russian/Русский

Доступны следующие режимы:

1. **_--ts_url_**, TorrServer url/ip.
2. **_--ts_port_**, TorrServer порт.
3. **_--secrets_**, путь к файлу secrets.
4. **_--kinozal_**, обновление торрентов напрямую с kinozal.tv(guru)(me) (нужна регистрация и логин/пароль прописать в [файл secrets](#файл-с-данными-для-аутентификации)).
5. **_--rutor_**, обновление торрентов напрямую с rutor.info(is) (регистрации не нужна).
6. **_--nnmclub_**, обновление торрентов напрямую с nnmclub.to (регистрации не нужна).
7. **_--torrentby_**, обновление торрентов напрямую с torrent.by (регистрации не нужна).
8. **_--rutracker_**, обновление торрентов напрямую с rutracker.org (регистрации не нужна).
9. **_--anilibria_**, обновление торрентов напрямую с anilibria.tv (регистрации не нужна).
10. **_--anidub_**, обновление торрентов напрямую с anidub.cocm (регистрации не нужна).
11. **_--newstudio_**, обновление торрентов напрямую с newstudio.tv (регистрации не нужна).
12. **_--piratbit_**, обновление торрентов напрямую с piratbit.org (регистрации не нужна).
13. **_--all_**, обновление по очереди для всех поддерживаемых трэкеров.
14. **_--litrcc_**,  обновление торрентов из RSS-ленты litr.cc (нужна регистрация на сайте litr.cc, после чего требуется взять UUID для RSS-ленты и указать в параметрах при запуске программы). Поддерживаются все трэкеры, поддерживаемые litr.cc. Торрент из RSS-ленты будет либо обновлен, либо автоматически добавлен в TorrServer если его там нет. Если торрент с таким же хэшем был добавлен через TorrServer Adder или вручную, то он будет перезаписан и в дальнейшем, обновления будут браться из RSS-ленты litr.cc.
15. **_--cleanup_**, режим для поиска и удаления старых торрентов с количеством серий, меньшим чем текущее, ищет все раздачи с одинаковым id, оставляет раздачу с наибольшим количеством серий, а остальные удаляет (пока поддерживаются только раздачи с rutor, которые добавлены либо через TorrServer Adder либо через RSS-ленту litr.cc).
16. **_--version_**, принудительная проверка новой версии на github с выводом ссылок на скачивание файлов, в любом случае покажет последний релиз (автоматическая проверка нового релиза проводится каждый вторник, вывод результата только при наличии нового релиза).
17. **_--proxy_**, прокси-сервер в формате: proxy-type://ip-address:port (proxy-type - http, https или socks5).
18. комбо-режим: можно указать сочетание из любых вышеперечисленных ключей (каждый из режимов может перезаписать торрент под себя и в последующем обновление будет происходить через данный режим, поэтому старайтесь избегать без лишней необходимости комбо-режим).


Программа распространяется как есть, баги и предложения по улучшению просьба добавлять в issues или писать на почту.

Процесс использования выглядит так: вы добавляете торрент с rutor.info(is)/nnmclub.to/torrent.by/kinozal.tv/rutracker.org в TorrServer через TorrServer Adder или добавляете торрент для мониторинга в litr.cc после чего периодически запускаете программу и она обновляет торренты если вышли новые серии сериала, сохраняя при этом отметки просмотренных серий.

## Установка

### Файл с данными для аутентификации

Файл формата json и с названием **secrets**, в папке рядом с исполняемым файлом или используйте параметр **--secrets** PATH_TO_FOLDER_WITH_SECRETS, поддерживается аутентификация для TorrServer и Kinozal.tv.

Пример содержимого:

`{"torrserver": {"user": "pass"}, "kinozal_id": {"user1": "pass1"}}`

с пустыми полями аутентификация не будет использоваться:

`{"torrserver": {"": ""}, "kinozal_id": {"": ""}}`

### Готовые бинарные файлы

Начиная с версии 0.2.2 можно скачать готовые исполняемые файлы для Linux/MacOS/Windows в разделе с релизами. Протестировано: Windows 11 Pro x64, Windows 10 Pro x64, Ubuntu 20.04, Ubuntu 22.04, Debian server 11, MacOS. Аргументы для запуска те же, что и для скрипта: `--cleanup/--rutor/--litrcc/--nnmclub/--torrentby --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT`.

### Для пользователей Windows

Скачиваем [Python](https://www.python.org/ftp/python/3.11.2/python-3.11.2.exe) и устанавливаем его, не забываем отметить при установке галку на **добавить путь в переменную PATH**. Далее [скачиваем последний релиз](https://github.com/Mantikor/TorrserverSeriesUpdater/releases), файл **SourceCode.zip** и распаковываем в удобную папку. Заходим в распакованную папку и по клику правой кнопкой запускаем терминал. В терминале набираем `pip3 install requirements.txt`, установятся нужные для работы пакеты. Далее запускаем скрипт: `python series_updater.py --litrcc RSS_FEED_UUID --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT` для обновления из RSS-ленты litr.cc или `python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT` для обновления с rutor. **TORRSERVER_URL** - адрес компьютера, где запущен TorrServer (например http://127.0.0.1, если на том же компьютере, откуда запускаете скрипт), **TORRSERVER_PORT** - порт, можно не указывать, если у вас порт по умолчанию **8090**.

Если на компьютере установлен Docker Desktop, то можно скачать уже готовый образ `mantik0r/torrserver_series_updater:latest` и запускать: `docker run --rm torrserver_series_updater:latest python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT`

### Для пользователей Linux

Запуск через скрипт работает так же как и для Windows: Python уже обычно есть в дистрибутиве, скрипт устанавливается так же как и для Windows.

### Docker

Скачиваем образ: `sudo docker pull mantik0r/torrserver_series_updater:latest` а потом запускаем: `sudo docker run --rm mantik0r/torrserver_series_updater:latest python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT`

Если вы хотите использовать файл secrets, вам нужно примонтировать папку с этим файлом при помощи параметра -v в команде запуска: `sudo docker run --rm -v LOCAL_FOLSER_WITH_SECRETS_FILE:FOLDER_INSIDE_CONTAINER mantik0r/torrserver_series_updater:latest python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT --secrets FOLDER_INSIDE_CONTAINER`

## English

There are following modes are available:

1. **_--ts_url_**, TorrServer url/ip.
2. **_--ts_port_**, TorrServer port.
3. **_--secrets_**, path to secrets file.
4. **_--kinozal_**, kinozal.tv direct torrents update (need registration and user/password in [secrets-file](#file-with-authentication-data)).
5. **_--rutor_**, rutor.info direct torrents update (no registration needed).
6. **_--nnmclub_**, nnmclub.to direct torrents update (no registration needed).
7. **_--torrentby_**, torrent.by direct torrents update (no registration needed).
8. **_--rutracker_**, rutracker.org direct torrents update (no registration needed).
9. **_--anilibria_**, anilibria.tv direct torrents update (no registration needed).
10. **_--anidub_**, anidub.cocm direct torrents update (no registration needed).
11. **_--newstudio_**, newstudio.tv direct torrents update (no registration needed).
12. **_--piratbit_**, piratbit.org direct torrents update (no registration needed).
13. **_--all_**, for update from all supported trackers.
14. **_--litrcc_**, torrents update from RSS-feed of litr.cc (you need registration on site, and you need RSS-feed UUID, you need to pass UUID to running parameters), supported all trackers supported by litr.cc, torrent will be updated or will be added to TorrServer. Torrents with same hash added by other modes may be overwritten and will be update with litrcc mode in the future.
15. **_--cleanup_**, mode for search and deletion old torrents, with fewer episodes than current. Will be search all torrents with the same id, leaves torrent with the most series, and deletes other (supported torrents from rutor, added with TorrServer Adder or RSS-feed litr.cc).
16. **_--version_**, force checking of new release version on github with display download links, in any case will display last release (automatic checking of new release will check on Tuesday, display result only if new release found).
17. **_--proxy_**, proxy-server string in format: proxy-type://ip-address:port (proxy-type - http, https or socks5).
18. combo-mode: use combination of all supported keys (each of the modes can rewrite the torrent for itself and in the future the update will occur through this mode, so try to avoid the combo mode without unnecessary need).

The program is distributed as is, bugs and suggestions for improvement you can add to issues or write to the e-mail.

## Installation

### File with authentication data

Json-format file with name **secrets**, in the folder with executable binary file or use parameter **--secrets** PATH_TO_FOLDER_WITH_SECRETS, supported authentication for TorrServer and Kinozal.tv.

Sample content:

`{"torrserver": {"user": "pass"}, "kinozal_id": {"user1": "pass1"}}`

with empty fields of user and password, authentication will not be used:

`{"torrserver": {"": ""}, "kinozal_id": {"": ""}}`

### Precompiled binary files

From version 0.2.2 you can download precompiled binary (executable) files for Linux/MacOS/Windows in release section. Tested on: Windows 11 Pro x64, Windows 10 Pro x64, Ubuntu 20.04, Ubuntu 22.04, Debian server 11, MacOS. Run arguments are the same for binary and for script: `--cleanup/--rutor/--litrcc/--nnmclub/--torrentby --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT`.


### Docker container

You need [Docker](https://docs.docker.com/engine/install/) preinstalled

Download image `sudo docker pull mantik0r/torrserver_series_updater:latest` and run it: `sudo docker run --rm mantik0r/torrserver_series_updater:latest python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT`

If you need to mount folder with secrets file inside, you should use -v parameter in run command: `sudo docker run --rm -v LOCAL_FOLSER_WITH_SECRETS_FILE:FOLDER_INSIDE_CONTAINER mantik0r/torrserver_series_updater:latest python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT --secrets FOLDER_INSIDE_CONTAINER`

### Python script

You need [Python 3.11](https://www.python.org/downloads/) or higher preinstalled

download archive with release or clone git repo

install requirements
```
pip3 install requirements.txt
```
run script
```
python series_updater.py --litrcc RSS_FEED_UUID --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```
or
```
python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```

## Running

### Docker container

#### Run update from litr.cc
```
sudo docker run --rm mantik0r/torrserver_series_updater:latest python series_updater.py --litrcc RSS_FEED_UUID --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```

#### Run update from rutor.info
```
sudo docker run --rm mantik0r/torrserver_series_updater:latest python series_updater.py --rutor --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```

#### Run update from nnmclub.to
```
sudo docker run --rm mantik0r/torrserver_series_updater:latest python series_updater.py --nnmclub --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```

#### Run cleanup mode
```
sudo docker run --rm mantik0r/torrserver_series_updater:latest python series_updater.py --cleanup --ts_url TORRSERVER_URL --ts_port TORRSERVER_PORT
```

**RSS_FEED_UUID**, like as 21100112-ffff-aaaa-cccc-e00110011fff - litr.cc RSS-feed identifier

**TORRSERVER_URL**, like as http://192.168.1.2 - ip address of TorrServer instance (default: **http://127.0.0.1**)

**TORRSERVER_PORT**, like as 8090 - port of TorrServer instance (default: **8090**)

### Python script

#### Run update from Litr.cc without settings file

`series_updater.py --litrcc 21100112-ffff-aaaa-cccc-e00110011fff --ts_url http://192.168.1.2`

#### Run update from Rutor without settings file

`series_updater.py --rutor --ts_url http://192.168.1.2`

#### Run cleanup mode

`series_updater.py --cleanup --ts_url http://192.168.1.2`

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

[TorrServer](https://github.com/YouROK/TorrServer)

[TorrServer Adder for Chrome](https://chrome.google.com/webstore/detail/torrserver-adder/ihphookhabmjbgccflngglmidjloeefg)

[TorrServer Adder for Firefox](https://addons.mozilla.org/ru/firefox/addon/torrserver-adder/)

[TorrServe client on 4PDA](https://4pda.to/forum/index.php?showtopic=889960)