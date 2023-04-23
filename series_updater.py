#!/usr/bin/python3
# -*- coding: utf-8 -*-
# coding: utf8

"""
Copyright: (c) 2023, Streltsov Sergey, straltsou.siarhei@gmail.com
init release 2023-02-10
The program for update torrents with new episodes for series

[TorrServer](https://github.com/YouROK/TorrServer)
[TorrServer Adder for Chrome](https://chrome.google.com/webstore/detail/torrserver-adder/ihphookhabmjbgccflngglmidjloeefg)
[TorrServer Adder for Firefox](https://addons.mozilla.org/ru/firefox/addon/torrserver-adder/)
[TorrServe client on 4PDA](https://4pda.to/forum/index.php?showtopic=889960)

"""


import requests
import os
import sys
import json
import logging
import argparse
import yaml
import re
from yarl import URL
from logging.handlers import RotatingFileHandler
from json import JSONDecodeError
from operator import itemgetter


__version__ = '0.4.2'


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s [%(funcName)s] - %(message)s',
                    handlers=[logging.StreamHandler()]
                    )

RUTOR = {'rutor_id': ['rutor.info', 'rutor.is']}
NNMCLUB = {'nnmclub_id': ['nnmclub.to']}
TORRENTBY = {'torrentby_id': ['torrent.by']}
TRACKERS = [RUTOR, NNMCLUB, TORRENTBY]


class TorrentsSource(object):
    def __init__(self, *args, **kwargs):
        # self.logger = logging.getLogger('_'.join([self.__class__.__name__, __version__]))
        # self.add_logger_handler(debug=kwargs.get('debug', False))
        self._server_url = kwargs.get('server_url', 'http://127.0.0.1')
        self.torrents_list: list = list()

    def add_logger_handler(self, debug=False):
        handlers = [logging.StreamHandler()]
        if debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(funcName)s] - %(message)s')
        logging.getLogger().setLevel(log_level)
        for handler in handlers:
            if handler == 'file':
                log_path = '/var/log/'
                prefix = self.__class__.__name__
                log_size = 2097152
                log_count = 2
                log_file = os.path.join(log_path, '_'.join([prefix, '.log']))
                file_handler = RotatingFileHandler(log_file, mode='a', maxBytes=log_size, backupCount=log_count,
                                                   encoding='utf-8', delay=False)
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logging.getLogger(prefix).addHandler(file_handler)

    def _server_request(self, r_type: str = 'get', pref: str = '', data: dict = None, timeout: int = 10,
                        verify: bool = True):
        if data is None:
            data = dict()
        if pref:
            pref = f'/{pref}'
        try:
            url = f'{self._server_url}{pref}'
            logging.debug(url)
            if r_type == 'get':
                resp = requests.get(url=url, timeout=timeout, verify=verify)
            elif r_type == 'post':
                resp = requests.post(url=url, json=data, timeout=timeout, verify=verify)
            else:
                resp = requests.head(url=url, json=data, timeout=timeout, verify=verify)
        except Exception as e:
            logging.error(e)
            logging.error(f'Connection problems with {self._server_url}{pref}')
            # raise Exception
            # sys.exit(1)
            resp = None
        return resp

    def get_torrent_page(self, torrent_id):
        self._server_url = f'{self._server_url}{torrent_id}'
        logging.debug(f'URL: {self._server_url}')
        resp = self._server_request(r_type='get')
        return resp

    def get_tracker_torrents(self, tracker_id=''):
        torrents = dict()
        for torrent in self.torrents_list:
            if torrent_id := torrent.get(tracker_id):
                lst_w_same_id = torrents.get(torrent_id, list())
                lst_w_same_id.append(torrent)
                torrents[torrent_id] = lst_w_same_id
        return torrents

    @staticmethod
    def is_tracker_link(url, patterns=None):
        if patterns is None:
            patterns = list
        if url and any(domain in url for domain in patterns):
            scratches = url.split('/')
            for part in scratches:
                if part.isdecimal():
                    return part
        return None


class TorrServer(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = URL(kwargs.get('ts_url'))
        self._server_url: URL = URL.build(scheme=self._server_url.scheme, host=self._server_url.host,
                                          port=kwargs.get('ts_port'))
        self.torrents_list: list = list()
        self._raw = self._get_torrents_list()
        self._raw2struct()

    def _get_torrents_list(self):
        resp = self._server_request(r_type='post', pref='torrents', data={'action': 'list'})
        return resp.json()

    def get_torrent_info(self, t_hash):
        resp = self._server_request(r_type='post', pref='viewed', data={'action': 'list', 'hash': t_hash})
        return resp.json()

    def remove_torrent(self, t_hash):
        resp = self._server_request(r_type='post', pref='torrents', data={'action': 'rem', 'hash': t_hash})
        return resp

    def add_torrent(self, torrent):
        data = {'action': 'add'} | torrent
        resp = self._server_request(r_type='post', pref='torrents', data=data)
        return resp

    def get_torrent(self, t_hash):
        resp = self._server_request(r_type='post', pref='torrents', data={'action': 'get', 'hash': t_hash})
        return resp

    def set_viewed(self, viewed):
        data = {'action': 'set'} | viewed
        resp = self._server_request(r_type='post', pref='viewed', data=data)
        return resp

    def _raw2struct(self):
        for i in self._raw:
            t_hash = i.get('hash')
            if t_hash:
                title = i.get('title')
                poster = i.get('poster')
                data = i.get('data')
                try:
                    data = json.loads(data)
                    t_url = data.get('TSA', dict()).get('srcUrl')
                except (JSONDecodeError, TypeError) as e:
                    logging.warning(data)
                    logging.warning(e)
                    t_url = data
                timestamp = i.get('timestamp')
                t_hash = i.get('hash')
                stat = i.get('stat')
                stat_string = i.get('stat_string')
                torrent_size = i.get('torrent_size')
                for tracker in TRACKERS:
                    tracker_name_id, tracker_url_patterns = list(tracker.items())[0]
                    torrent_id = TorrentsSource.is_tracker_link(url=t_url, patterns=tracker_url_patterns)
                    if torrent_id:
                        torrent = {'title': title, 'poster': poster, 't_url': t_url, 'timestamp': timestamp,
                                   't_hash': t_hash, 'stat': stat, 'stat_string': stat_string,
                                   'torrent_size': torrent_size, tracker_name_id: torrent_id}
                        self.torrents_list.append(torrent)
                        continue
        logging.info(f'Torrserver, torrents got: {len(self.torrents_list)}')

    def add_updated_torrent(self, updated_torrent, viewed_episodes):
        res = self.add_torrent(torrent=updated_torrent)
        title = updated_torrent.get('title')
        t_hash = updated_torrent.get('hash')
        if res.status_code == 200:
            logging.info(f'{title} => added/updated')
        for idx in viewed_episodes:
            viewed = {'hash': t_hash, 'file_index': idx}
            res = self.set_viewed(viewed=viewed)
            if res.status_code == 200:
                logging.info(f'{idx} episode => set as viewed')
        res = self.get_torrent(t_hash=t_hash)
        return res.status_code

    def get_torrent_stat(self, t_hash):
        resp = self._server_request(r_type='get', pref=f'stream/fname?link={t_hash}&stat')
        return resp

    def delete_torrent_with_check(self, t_hash):
        res = self.remove_torrent(t_hash=t_hash)
        res2 = self.get_torrent(t_hash=t_hash)
        if (res.status_code == 200) and (res2.status_code == 404):
            logging.info(f'Old torrent with hash: {t_hash} => deleted successfully')
        else:
            logging.warning(f'Old torrent with hash: {t_hash} => deletion problems')

    def cleanup_torrents(self, hashes=None, perm=False):
        if hashes is None:
            hashes = list()
        if perm:
            logging.warning(f'Permanent cleanup mode!!! Will be deleted torrents duplicates.')

            tracker_name_id, tracker_url_patterns = list(RUTOR.items())[0]
            rutor_torrents = self.get_tracker_torrents(tracker_id=tracker_name_id)
            logging.info(f'{len(rutor_torrents)} torrents from {tracker_url_patterns} found.')
            duplicated = 0
            for rutor_id, torrents_lst in rutor_torrents.items():
                if len(torrents_lst) > 1:
                    duplicated += 1
                    logging.info(f'ID: {rutor_id}, {len(torrents_lst)} copies found.')
                    doubles = list()
                    for torrent in torrents_lst:
                        logging.debug(torrent)
                        t_hash = torrent.get('t_hash')
                        stat_resp = self.get_torrent_stat(t_hash=t_hash)
                        if stat_resp.status_code == 200:
                            stat_json = stat_resp.json()
                            if stat_json:
                                title = stat_json.get('title')
                                file_stats = stat_json.get('file_stats', list())
                                logging.info(f'{title} ==> {len(file_stats)} series.')
                                doubles.append({'hash': t_hash, 'title': title, 'file_stats': file_stats})
                        else:
                            logging.error(
                                f'Error getting info about torrent file list, STATUS_CODE={stat_resp.status_code}')
                    logging.info(f'Will search newest one.')
                    doubles = sorted(doubles, key=lambda d: len(d['file_stats']), reverse=True)
                    while len(doubles) > 1:
                        deletion_candidate = doubles.pop(-1)
                        logging.debug(deletion_candidate)
                        self.delete_torrent_with_check(t_hash=deletion_candidate.get('hash'))
            if not duplicated:
                logging.info(f'There are no duplicates found. Have a nice day!')
        else:
            for hash_to_remove in hashes:
                self.delete_torrent_with_check(t_hash=hash_to_remove)


class RuTor(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = 'http://rutor.info/torrent/'

    @staticmethod
    def get_magnet(text):
        pattern = re.compile(r'<div id=\"download\"><a href=\"magnet:\?xt=urn:btih:([a-f0-9]{40})')
        html = text.replace('\n', '')
        search_res = pattern.search(html)
        if search_res:
            return search_res.group(1)
        else:
            return None

    @staticmethod
    def get_title(text):
        pattern = re.compile(r'<h1>(.*?)</h1>')
        html = text.replace('\n', '')
        search_res = pattern.search(html)
        if search_res:
            return search_res.group(1)
        else:
            return None

    @staticmethod
    def get_poster(text):
        html = text.replace('\n', '').replace('\r', '').replace('\t', '')
        match = re.search(r'<br /><img src=[\'"]?([^\'" >]+)', html)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def is_tracker_link(url, patterns=None):
        if patterns is None:
            patterns = list
        if url and any(domain in url for domain in ['rutor.info', 'rutor.is']):
            scratches = url.split('/')
            for part in scratches:
                if part.isdecimal():
                    return part
        return None


class LitrCC(TorrentsSource):
    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = URL(url)
        # self.torrents_list: list = list()
        self._raw = self._get_torrents_list()
        self._raw2struct()

    def _get_torrents_list(self):
        resp = self._server_request(r_type='get')
        return resp.json()

    def check_rutor_url(self):
        pass

    def get_list_of_groups(self):
        pass

    def add_torrent_to_listener(self, secret, group_id):
        pass

    def refresh_token(self, token):
        # ToDO: save last valid token for next auth (refresh)
        pass

    def _raw2struct(self):
        for i in self._raw.get('items', list()):
            # ToDO: RSS contains new and old torrents (not only new), need to catch newest one
            t_id = i.get('id')
            if t_id:
                title = i.get('title')
                url = i.get('url')
                date_modified = i.get('date_modified')
                image = i.get('image')
                external_url = i.get('external_url')
                torrent = {'id': str(t_id).lower(), 'title': title, 'url': url, 'date_modified': date_modified,
                           'image': image, 'external_url': external_url}
                self.torrents_list.append(torrent)
                logging.debug(f'litr.cc: {str(t_id).lower()}')
                logging.debug(f'litr.cc: {title}')
                logging.debug(f'litr.cc: {external_url}')
                logging.debug('='*150)
        logging.info(f'Litr.cc, torrents got: {len(self.torrents_list)}')


class Config:
    def __init__(self, filename):
        self._filename = filename
        self.config = dict()
        self.get_settings_path()
        self.load_config()

    def load_config(self):
        with open(self._filename, 'r') as f:
            try:
                self.config = yaml.load(f, Loader=yaml.FullLoader)
                logging.info(f'Settings loaded from file: {self._filename}')
            except Exception as e:
                logging.error(f'{e}, problem with {self._filename} file')
                logging.warning('Will be used default settings!!!')

    def save_config(self):
        pass

    def get_settings_path(self):
        search_paths = ['', os.path.dirname(os.path.abspath(__file__)),
                        os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))]
        for search_path in search_paths:
            full_path = os.path.join(search_path, self._filename)
            if os.path.isfile(full_path):
                self._filename = full_path
                break


class NnmClub(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = 'https://nnmclub.to/forum/viewtopic.php?t='

    @staticmethod
    def get_magnet(text):
        pattern = re.compile(r'<a rel=\"nofollow\" href=\"magnet:\?xt=urn:btih:([a-fA-F0-9]{40})')
        html = text.replace('\n', '')
        search_res = pattern.search(html)
        if search_res:
            return search_res.group(1).lower()
        else:
            return None

    @staticmethod
    def get_title(text):
        pattern = re.compile(r'<a class=\"maintitle\" href="viewtopic.php\?t=([0-9]*)\">(.*?)</a>')
        html = text.replace('\n', '')
        search_res = pattern.search(html)
        if search_res:
            return search_res.group(2)
        else:
            return None

    @staticmethod
    def get_poster(text):
        html = text.replace('\n', '').replace('\r', '').replace('\t', '')
        match = re.search(r'<meta property=\"og:image" content=[\'"]?([^\'" >]+)', html)
        if match:
            return match.group(1)
        else:
            return None


class TorrentBy(RuTor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = 'https://torrent.by/'

    # if you have problems with error ssl certificate torrent.by, pass verify=False to disable verify ssl certificate
    def get_torrent_page(self, torrent_id):
        self._server_url = f'{self._server_url}{torrent_id}'
        logging.debug(f'URL: {self._server_url}')
        resp = self._server_request(r_type='get', verify=False)
        return resp

    @staticmethod
    def get_magnet(text):
        pattern = re.compile(r'<a href=\"magnet:\?xt=urn:btih:([a-f0-9]{40})')
        html = text.replace('\n', '')
        search_res = pattern.search(html)
        if search_res:
            return search_res.group(1)
        else:
            return None


class ArgsParser:
    def __init__(self, desc, def_settings_file=None):
        self.parser = argparse.ArgumentParser(description=desc, add_help=True)
        self.parser.add_argument('--settings', action='store', dest='settings', type=str, default=def_settings_file,
                                 help='settings file for future purposes')
        self.parser.add_argument('--ts_url', action='store', dest='ts_url', type=str, default='http://127.0.0.1',
                                 help='torrserver url')
        self.parser.add_argument('--ts_port', action='store', dest='ts_port', type=int, default=8090,
                                 help='torrserver port')
        self.parser.add_argument('--litrcc', action='store', dest='litrcc', type=str, default='',
                                 help='feed uuid from litr.cc')
        self.parser.add_argument('--rutor', action='store_true', dest='rutor', default=False,
                                 help='update torrents from rutor.info')
        self.parser.add_argument('--nnmclub', action='store_true', dest='nnmclub', default=False,
                                 help='update torrents from nnmclub.to')
        self.parser.add_argument('--torrentby', action='store_true', dest='torrentby', default=False,
                                 help='update torrents from torrent.by')
        self.parser.add_argument(
            '--cleanup', action='store_true', dest='cleanup', default=False,
            help='Cleanup mode: merge separate torrents with different episodes for same series to one torrent')
        self.parser.add_argument('--debug', action='store_true', dest='debug', default=False,
                                 help='Enable DEBUG log level')

    @property
    def args(self):
        return self.parser.parse_args()


def update_tracker_torrents(tracker, tracker_class, torrserver):
    tracker_name_id, tracker_url_patterns = list(tracker.items())[0]
    tracker_torrents = torrserver.get_tracker_torrents(tracker_id=tracker_name_id)
    for torrent_id, torrents_list in tracker_torrents.items():
        cls = tracker_class()
        resp = cls.get_torrent_page(torrent_id=torrent_id)
        if resp and resp.status_code == 200:
            t_title = cls.get_title(text=resp.text)
            t_hash = cls.get_magnet(text=resp.text)
            t_poster = cls.get_poster(text=resp.text)
            logging.info(f'Checking: {t_title}')
            logging.debug(f'Poster: {t_poster}')
            logging.debug(f'New HASH: {t_hash}')
            hashes = list()
            for i in torrents_list:
                old_hash = i.get('t_hash')
                hashes.append(old_hash)
            if t_hash not in hashes:
                logging.info(f'Found update: {t_hash}')
                indexes = set()
                data = f'{{"TSA":{{"srcUrl":"{cls._server_url}"}}}}'
                for torrent_hash in hashes:
                    viewed_indexes_list = torrserver.get_torrent_info(t_hash=torrent_hash)
                    for vi in viewed_indexes_list:
                        indexes.add(vi.get('file_index'))

                updated_torrent = {'link': f'magnet:?xt=urn:btih:{t_hash}', 'title': t_title, 'poster': t_poster,
                                   'save_to_db': True, 'data': data, 'hash': t_hash}
                torrserver.add_updated_torrent(updated_torrent=updated_torrent, viewed_episodes=indexes)
                torrserver.cleanup_torrents(hashes=hashes)
            else:
                logging.info(f'No updates found: {t_hash}')


def main():
    desc = f'Awesome series updater for TorrServer, (c) 2023 Mantikor, version {__version__}'
    logging.info(desc)
    ts = ArgsParser(desc=desc, def_settings_file=None)
    if ts.args.settings:
        # ToDO: add settings flow
        settings = Config(filename=ts.args.settings)

    torr_server = TorrServer(**{k: v for k, v in vars(ts.parser.parse_args()).items()})

    if ts.args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if ts.args.cleanup:
        torr_server.cleanup_torrents(perm=True)

    if ts.args.rutor:
        update_tracker_torrents(tracker=RUTOR, tracker_class=RuTor, torrserver=torr_server)

    if ts.args.litrcc:
        litrcc_rss_feed_url = f'https://litr.cc/feed/{ts.args.litrcc}/json'
        litrcc = LitrCC(url=litrcc_rss_feed_url)
        logging.info(f'Litr.cc RSS uuid: {ts.args.litrcc}')
        tracker_name_id, tracker_url_patterns = list(RUTOR.items())[0]
        litrcc_rutor_torrents = litrcc.get_tracker_torrents(tracker_id=tracker_name_id)
        ts_rutor_torrents = torr_server.get_tracker_torrents(tracker_id=tracker_name_id)
        for lcc_rutor_id, lcc_torrent_list in litrcc_rutor_torrents.items():
            sorted_lst = sorted(lcc_torrent_list, key=itemgetter('date_modified'), reverse=True)
            litrcc_rutor_torrents[lcc_rutor_id] = sorted_lst
            ts_torrents_list = ts_rutor_torrents.get(lcc_rutor_id, list())
            hashes = list()
            for i in ts_torrents_list:
                old_hash = i.get('t_hash')
                hashes.append(old_hash)
            lcc_rutor_torrent = litrcc_rutor_torrents[lcc_rutor_id][0]
            lcc_link = lcc_rutor_torrent.get('id')
            lcc_title = lcc_rutor_torrent.get('title')
            lcc_poster = lcc_rutor_torrent.get('image')
            logging.info(f'Checking: {lcc_title}')
            logging.debug(f'Poster: {lcc_poster}')
            logging.debug(f'New HASH: {lcc_link}')
            if lcc_link not in hashes:
                logging.info(f'Found update: {lcc_link}')
                indexes = set()
                data = f'{{"TSA":{{"srcUrl":"http://rutor.info/torrent/{lcc_rutor_id}"}}}}'
                for t_hash in hashes:
                    viewed_indexes_list = torr_server.get_torrent_info(t_hash=t_hash)
                    for vi in viewed_indexes_list:
                        indexes.add(vi.get('file_index'))
                updated_torrent = {'link': f'magnet:?xt=urn:btih:{lcc_link}', 'title': lcc_title, 'poster': lcc_poster,
                                   'save_to_db': True, 'data': data, 'hash': lcc_link}
                torr_server.add_updated_torrent(updated_torrent=updated_torrent, viewed_episodes=indexes)
                torr_server.cleanup_torrents(hashes=hashes)
            else:
                logging.info(f'No new episodes found: {lcc_link}')

    if ts.args.nnmclub:
        update_tracker_torrents(tracker=NNMCLUB, tracker_class=NnmClub, torrserver=torr_server)

    if ts.args.torrentby:
        update_tracker_torrents(tracker=TORRENTBY, tracker_class=TorrentBy, torrserver=torr_server)


if __name__ == '__main__':
    main()
