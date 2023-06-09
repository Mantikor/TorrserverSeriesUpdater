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
import bencodepy
import hashlib
from yarl import URL
from logging.handlers import RotatingFileHandler
from json import JSONDecodeError
from datetime import datetime
from lxml import html


__version__ = '0.10.7'


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()]
                    )

RUTOR = {'rutor_id': ['rutor.info', 'rutor.is'], 'sep': '/'}
NNMCLUB = {'nnmclub_id': ['nnmclub.to'], 'sep': '='}
TORRENTBY = {'torrentby_id': ['torrent.by'], 'sep': '/'}
KINOZAL = {'kinozal_id': ['kinozal.tv', 'kinozal.guru', 'kinozal.me'], 'sep': '='}
RUTRACKER = {'rutracker_id': ['rutracker.org'], 'sep': '='}
ANIDUB = {'anidub_id': ['anidub.com'], 'sep': ''}
ANILIBRIA = {'anilibria_id': ['anilibria.tv'], 'sep': ''}

TRACKERS = [RUTOR, NNMCLUB, TORRENTBY, KINOZAL, RUTRACKER, ANIDUB, ANILIBRIA]


class TorrentsSource(object):
    def __init__(self, *args, **kwargs):
        self.unknown_response = type('obj', (object,), {'status_code': 520, 'reason': 'Unknown Error', 'text': ''})
        self._server_url = None
        self._secrets: dict = dict()
        self._url_pattern = kwargs.get('server_url', 'http://127.0.0.1')
        self._session = requests.Session()
        self.torrents_list: list = list()
        self._login = None
        self._password = None
        self._proxy = kwargs.get('proxy', dict())
        if self._proxy:
            self._session.proxies = {'http': self._proxy, 'https': self._proxy}

    def _get_auth(self):
        self._session.auth = (self._login, self._password)

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

    @property
    def secrets(self):
        return self._secrets

    @staticmethod
    def load_secrets(filename='secrets'):
        """Load secrets from json file

        :return: result: dictionary with login/password pair for each tracker with auth
        """
        search_paths = ['./', os.path.dirname(os.path.abspath(__file__)),
                        os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))]
        if getattr(sys, 'frozen', False):
            search_paths.append(os.path.dirname(sys.executable))
        logging.debug(f'Search paths: {search_paths}')
        for search_path in set(search_paths):
            full_path = os.path.join(search_path, filename)
            if os.path.isfile(full_path):
                with open(full_path, mode='r', encoding='utf-8') as secrets_file:
                    try:
                        result = json.load(secrets_file)
                        logging.info(f'Secrets loaded from file: {full_path}')
                        logging.debug(f'{result}')
                        return result
                    except json.decoder.JSONDecodeError:
                        logging.error(f'{full_path} is not a valid json file')
                        logging.warning('No secrets loaded!')
                        return dict()
        logging.warning(f'File: {filename} not found on paths: {search_paths}, or file format not valid')
        logging.warning('No secrets loaded!')
        return dict()

    def _server_request(self, r_type: str = 'get', url=None, pref: str = '', data: dict = None, timeout: int = 10,
                        verify: bool = True):
        if data is None:
            data = dict()
        if pref:
            pref = f'/{pref}'
        if url is None:
            url = f'{self._server_url}{pref}'
        logging.debug(f'Proxy settings: {self._session.proxies}')
        try:
            logging.debug(url)
            if r_type == 'get':
                resp = self._session.get(url=url, timeout=timeout, verify=verify)
            elif r_type == 'post':
                resp = self._session.post(url=url, json=data, timeout=timeout, verify=verify)
            else:
                resp = self._session.head(url=url, json=data, timeout=timeout, verify=verify)
        except Exception as e:
            logging.error(e)
            logging.error(f'Connection problems with {url}')
            # raise Exception
            # sys.exit(1)
            resp = self.unknown_response
        return resp

    def server_request(self, *args, **kwargs):
        return self._server_request(*args, **kwargs)

    def get_torrent_page(self, torrent_id):
        resp = None
        if self._url_pattern:
            self._server_url = f'{self._url_pattern}{torrent_id}'
            logging.debug(f'URL: {self._server_url}')
            resp = self._server_request(r_type='get')
        return resp

    @staticmethod
    def get_hash_from_magnet(magnet_link):
        if magnet_link:
            search_pattern = re.compile(r'magnet:\?xt=urn:btih:([a-f0-9]{40})')
            search_res = search_pattern.search(magnet_link)
            if search_res:
                return search_res.group(1)
            else:
                return None

    def get_tracker_torrents(self, tracker_id=''):
        torrents = dict()
        for torrent in self.torrents_list:
            if torrent_id := torrent.get(tracker_id):
                lst_w_same_id = torrents.get(torrent_id, list())
                lst_w_same_id.append(torrent)
                torrents[torrent_id] = lst_w_same_id
        return torrents

    @staticmethod
    def is_tracker_link(url, patterns=None, sep='/'):
        if patterns is None:
            patterns = list
        if url and any(domain in url for domain in patterns):
            if sep:
                try:
                    clean_url = url.split('&')[0]
                    scratches = clean_url.split(sep)
                    for part in scratches:
                        if part.isdecimal():
                            return part
                except Exception as e:
                    logging.error(e)
                    return None
            else:
                return url
        return None


class TorrServer(TorrentsSource):

    tracker_id = 'torrserver'

    def __init__(self, *args, **kwargs):
        # self._secrets = self.load_secrets()
        super().__init__(*args, **kwargs)
        self._session.proxies = dict()
        self._server_url = URL(kwargs.get('ts_url'))
        self._server_url: URL = URL.build(scheme=self._server_url.scheme, host=self._server_url.host,
                                          port=kwargs.get('ts_port'))
        self._secrets = self.load_secrets()
        self._login, self._password = list(self.secrets.get(self.tracker_id, {None: None}).items())[0]
        if self._login and self._password:
            self._get_auth()
        else:
            logging.warning(f'Login: {self._login} and/or password: {self._password} is empty, '
                            f'auth on {self.tracker_id} switched off')

        self.torrents_list: list = list()
        self.litrcc_torrents_list: list = list()
        self.litrcc_torrents_cache: list = list()
        self._raw = self._get_torrents_list()
        self._raw2struct()

    @property
    def secrets(self):
        return self._secrets

    def _get_torrents_list(self):
        resp = self._server_request(r_type='post', pref='torrents', data={'action': 'list'})
        if resp.status_code == 200:
            return resp.json()
        else:
            logging.warning('{}, {}'.format(resp.status_code, resp.reason))
            return dict()

    def get_torrent_info(self, t_hash):
        resp = self._server_request(r_type='post', pref='viewed', data={'action': 'list', 'hash': t_hash})
        if resp.status_code == 200:
            return resp.json()
        else:
            logging.warning('{}, {}'.format(resp.status_code, resp.reason))
            return dict()

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
                    _, sep = list(tracker.items())[1]
                    torrent_id = TorrentsSource.is_tracker_link(url=t_url, patterns=tracker_url_patterns, sep=sep)
                    if torrent_id:
                        torrent = {'title': title, 'poster': poster, 't_url': t_url, 'timestamp': timestamp,
                                   't_hash': t_hash, 'stat': stat, 'stat_string': stat_string,
                                   'torrent_size': torrent_size, tracker_name_id: torrent_id}
                        self.torrents_list.append(torrent)
                        continue
        logging.info(f'Torrserver, torrents got: {len(self.torrents_list)}')

    def get_litrcc_torrents(self):
        for i in self._raw:
            t_hash = i.get('hash')
            if t_hash:
                title = i.get('title')
                poster = i.get('poster')
                data = i.get('data')
                try:
                    data = json.loads(data)
                    t_url = data.get('LITRCC', dict()).get('external_url')
                except (JSONDecodeError, TypeError) as e:
                    logging.warning(data)
                    logging.warning(e)
                    t_url = None
                timestamp = i.get('timestamp')
                t_hash = i.get('hash')
                stat = i.get('stat')
                stat_string = i.get('stat_string')
                torrent_size = i.get('torrent_size')
                if t_url:
                    torrent = {'title': title, 'poster': poster, 't_url': t_url, 'timestamp': timestamp,
                               't_hash': t_hash, 'stat': stat, 'stat_string': stat_string,
                               'torrent_size': torrent_size}
                    self.litrcc_torrents_list.append(torrent)
                    self.litrcc_torrents_cache.append(t_url)
        logging.info(f'Torrserver, litr.cc torrents got: {len(self.litrcc_torrents_list)}')

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
        self._url_pattern = 'http://rutor.info/torrent/'

    @staticmethod
    def get_magnet(text):
        links = html.fromstring(text).xpath('//div[@id="download"]/a/@href')
        for link in links:
            if 'magnet' in link:
                return link
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


class LitrCC(TorrentsSource):
    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = URL(url)
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
        filtered_data = dict()
        for i in self._raw.get('items', list()):
            t_id = i.get('id')
            if t_id:
                title = i.get('title')
                url = i.get('url')
                date_modified = i.get('date_modified')
                image = i.get('image')
                external_url = i.get('external_url')
                torrent = {'id': str(t_id).lower(), 'title': title, 'url': url, 'date_modified': date_modified,
                           'image': image, 'external_url': external_url}
                old = filtered_data.get(external_url)
                if external_url:
                    if old:
                        old_date_modified = old.get('date_modified')
                        old_date_modified_iso = datetime.fromisoformat(old_date_modified)
                        date_modified_iso = datetime.fromisoformat(date_modified)
                        if old_date_modified_iso < date_modified_iso:
                            filtered_data[external_url] = torrent
                    else:
                        filtered_data[external_url] = torrent
        for _, v in filtered_data.items():
            self.torrents_list.append(v)
        logging.info(f'litr.cc RSS-feed, torrents got: {len(self.torrents_list)}')


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
        self._url_pattern = 'https://nnmclub.to/forum/viewtopic.php?t='

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
        self._url_pattern = 'https://torrent.by/'

    # if you have problems with error ssl certificate torrent.by, pass verify=False to disable verify ssl certificate
    def get_torrent_page(self, torrent_id):
        self._server_url = f'{self._url_pattern}{torrent_id}'
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


class Kinozal(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._t_hash = None
        self._url_pattern = 'https://kinozal.tv/details.php?id='
        self._login_url = 'https://kinozal.tv/takelogin.php'
        self._login, self._password = list(kwargs.get('secrets', dict()).get('kinozal_id', {None: None}).items())[0]
        if self._login and self._password:
            self._get_auth()
        else:
            logging.warning(f'Auth problem: login: {self._login}, password: {self._password}, url: {self._login_url}')

    def _get_auth(self):
        data = {'username': self._login, 'password': self._password, 'returnto': ''}
        logging.debug(f'login: {self._login}, password: {self._password}')
        # ToDo: catch errors on connect, like as timeout
        self._server_request(r_type='post', url=self._login_url, data=data)
        # self._session.post(url=self._login_url, data=data)

    def get_torrent_page(self, torrent_id):
        if self._session:
            self._server_url = f'{self._url_pattern}{torrent_id}'
            logging.debug(f'URL: {self._server_url}')
            resp = self._server_request(url=f'https://kinozal.tv/get_srv_details.php?id={torrent_id}&action=2')
            # resp = self._session.get(url=f'https://kinozal.tv/get_srv_details.php?id={torrent_id}&action=2')
            pattern = re.compile(r': ([a-fA-F0-9]{40})</li>')
            search_res = pattern.search(resp.text)
            if search_res:
                self._t_hash = search_res.group(1).lower()
            else:
                self._t_hash = None
            resp = self._server_request(url=self._server_url)
            # resp = self._session.get(url=self._server_url)
        else:
            resp = None
        return resp

    def get_magnet(self, text):
        return self._t_hash

    @staticmethod
    def get_title(text):
        meta_og_title = html.fromstring(text).xpath('//meta[@property="og:title"]/@content')
        if meta_og_title:
            return meta_og_title[0]
        else:
            return None

    @staticmethod
    def get_poster(text):
        logo_href = html.fromstring(text).xpath('//div[@class="logo_new"]/a/@href')
        if logo_href:
            domain = logo_href[0]
        else:
            domain = 'https://kinozal.tv'
        meta_og_image = html.fromstring(text).xpath('//meta[@property="og:image"]/@content')
        if meta_og_image:
            img_link_path = meta_og_image[0]
            if 'http' in img_link_path:
                return img_link_path
            else:
                return domain + img_link_path
        else:
            return None


class Rutracker(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url_pattern = 'https://rutracker.org/forum/viewtopic.php?t='

    @staticmethod
    def get_magnet(text):
        magnet_link = html.fromstring(text).xpath('//a[@class="magnet-link"]/@href')
        if magnet_link:
            magnet_link_href = magnet_link[0]
            magnet_pattern = re.compile(r'magnet:\?xt=urn:btih:([a-fA-F0-9]{40})')
            search_res = magnet_pattern.search(magnet_link_href)
            if search_res:
                return search_res.group(1).lower()
        else:
            return None

    @staticmethod
    def get_title(text):
        h1_maintitle = html.fromstring(text).xpath('//h1[@class="maintitle"]/a[@id="topic-title"]//text()')
        if h1_maintitle:
            h1_maintitle_text = ''.join(h1_maintitle)
            return h1_maintitle_text
        else:
            return None

    @staticmethod
    def get_poster(text):
        img_src = html.fromstring(text).xpath('//var[contains(@class, "postImg postImgAligned")]/@title')
        if img_src:
            return img_src[0]
        else:
            return None


class Updater(TorrentsSource):

    def __init__(self, *args, **kwargs):
        # self._secrets = self.load_secrets()
        super().__init__(*args, **kwargs)
        self.schedule = kwargs.get('schedule', -1)
        self._server_url = 'https://api.github.com'

    def _get_latest_releases(self):
        resp = self._server_request(r_type='get', pref='repos/Mantikor/TorrserverSeriesUpdater/releases/latest')
        if resp.status_code == 200:
            return resp.json()
        else:
            logging.warning('{}, {}'.format(resp.status_code, resp.reason))
            return dict()

    @staticmethod
    def is_there_new_version(remote_v, local_v=__version__):
        pattern = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
        search_res = pattern.search(local_v)
        if search_res:
            local_version = search_res.group(0)
        else:
            local_version = '0.0.0'
        search_res = pattern.search(remote_v)
        if search_res:
            remote_version = search_res.group(0)
        else:
            remote_version = '0.0.0'
        local_version = local_version.split('.')
        remote_version = remote_version.split('.')
        for local_sub_v, remote_sub_v in list(zip(local_version, remote_version)):
            if local_sub_v < remote_sub_v:
                return True
        return False

    def check_updates(self, only_new=True):
        releases = self._get_latest_releases()
        ver = releases.get('tag_name')
        comment = releases.get('name')
        new_version = self.is_there_new_version(remote_v=ver)
        if new_version:
            logging.info(f'Found new release: {ver}')
            logging.info(f'{comment}')
        elif not only_new:
            logging.info(f'Current version on github: {ver}')
            logging.info(f'{comment}')
            r_assets = releases.get('assets', list())
            for asset in r_assets:
                download_url = asset.get('browser_download_url')
                logging.info(f'{download_url}')

    def check_scheduled_updates(self, schedule):
        dt = datetime.now()
        today = dt.isoweekday()
        if schedule == today:
            self.check_updates()


class TorrentFile(object):
    def __init__(self, file_content):
        self.content = file_content
        try:
            self.metadata = bencodepy.decode(self.content)
        except Exception as e:
            logging.error(e)
            self.metadata = dict()

    def get_hash(self):
        try:
            subj = self.metadata[b'info']
            hash_contents = bencodepy.encode(subj)
            hex_digest = hashlib.sha1(hash_contents).hexdigest()
        except Exception as e:
            logging.error(e)
            hex_digest = None
        return hex_digest

    def get_name(self):
        try:
            b_name = self.metadata[b'info'][b'name']
            name = b_name.decode('utf-8')
        except Exception as e:
            logging.error(e)
            name = None
        return name

    def get_files_list(self):
        pass


class AniDub(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url_pattern = ''
        self._file_links_xpath = '//div[@class="torrent"]//div[@class="torrent_h"]/a/@href'

    def get_torrent_page(self, torrent_id):
        self._server_url = torrent_id
        logging.debug(f'URL: {self._server_url}')
        resp = self._server_request(r_type='get')
        return resp

    def get_magnet(self, text, torrent_name):
        """Get magnet from .torrent files links of html page
        Get all links to .torrent files on page (from text), download .torrent file,
        get metadata from file, from metadata get torrent name (metadata[b'info'][b'name']),
        if name == torrent_name get hash from .torrent file

        :return: file_hash:
        """
        page = html.fromstring(text)
        page.make_links_absolute(self._server_url)
        file_links = page.xpath(self._file_links_xpath)
        if file_links:
            file_links = set(file_links)
            for f_link in file_links:
                temp_file = TorrentsSource()
                logging.debug(f'Link: {f_link}')
                torrent_file = temp_file.server_request(url=f_link)
                if torrent_file:
                    tf = TorrentFile(file_content=torrent_file.content)
                    file_torrent_name = tf.get_name()
                    logging.debug(f'File  torrent name: {file_torrent_name}')
                    logging.debug(f'Given torrent name: {file_torrent_name}')
                    if file_torrent_name == torrent_name:
                        file_hash = tf.get_hash()
                        logging.debug(f'Torrent hash from downloaded file: {file_hash}')
                        return file_hash
        return None

    @staticmethod
    def get_title(text):
        title = html.fromstring(text).xpath('//h1//text()')
        if title:
            return title[0]
        else:
            return None

    @staticmethod
    def get_poster(text):
        img_src = html.fromstring(text).xpath('//div[contains(@class, "poster_bg")]//img/@src')
        if img_src:
            return img_src[0]
        else:
            return None


class AniLibria(AniDub):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_links_xpath = '//div[@class="download-torrent"]//a[@class="torrent-download-link"]/@href'

    @staticmethod
    def get_title(text):
        title = html.fromstring(text).xpath('//head/title/text()')
        if title:
            return title[0]
        else:
            return None

    def get_poster(self, text):
        page = html.fromstring(text)
        page.make_links_absolute(self._server_url)
        img_src = page.xpath('//img[@class="detail_torrent_pic"]/@src')
        if img_src:
            return img_src[0]
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
        self.parser.add_argument('--kinozal', action='store_true', dest='kinozal', default=False,
                                 help='update torrents from kinozal.tv')
        self.parser.add_argument('--rutracker', action='store_true', dest='rutracker', default=False,
                                 help='update torrents from rutracker.org')
        self.parser.add_argument('--all', action='store_true', dest='all', default=False,
                                 help='update torrents from all trackers: rutor, nnmclub, tby, kinozal, rutracker')
        self.parser.add_argument('--version', action='store_true', dest='version', default=False,
                                 help='check updates and new releases on github page')
        self.parser.add_argument('--proxy', action='store', dest='proxy', type=str, default='',
                                 help='proxy server string in format: proxy-type://ip-address:port')
        self.parser.add_argument('--anidub', action='store_true', dest='anidub', default=False,
                                 help='update torrents from anidub.com')
        self.parser.add_argument('--anilibria', action='store_true', dest='anilibria', default=False,
                                 help='update torrents from anilibria.tv')
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
    logging.info(f'Tracker: {tracker_url_patterns}; found torrents: {len(tracker_torrents)}')
    for torrent_id, torrents_list in tracker_torrents.items():
        cls = tracker_class
        resp = cls.get_torrent_page(torrent_id=torrent_id)
        if resp and resp.status_code == 200:
            t_title = cls.get_title(text=resp.text)
            if isinstance(cls, AniDub):
                fl_torrent = torrents_list[0]
                fl_t_hash = fl_torrent.get('t_hash')
                fl_t_info = torrserver.get_torrent_stat(t_hash=fl_t_hash)
                if fl_t_info.status_code == 200:
                    fl_t_name = fl_t_info.json().get('name')
                    t_hash = cls.get_magnet(text=resp.text, torrent_name=fl_t_name)
                else:
                    t_hash = None
            else:
                t_hash = cls.get_magnet(text=resp.text)
            t_poster = cls.get_poster(text=resp.text)
            # logging.info(f'Checking: {t_title}')
            logging.debug(f'Poster: {t_poster}')
            logging.debug(f'New HASH: {t_hash}')
            hashes = list()
            for i in torrents_list:
                old_hash = i.get('t_hash')
                hashes.append(old_hash)
            if t_hash and (t_hash not in hashes):
                logging.info(f'{torrents_list[0].get("title")}')
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
                logging.info(f'{t_title}')
                logging.info(f'No updates found: {t_hash}')


def main():
    desc = f'Awesome series updater for TorrServer, (c) 2023 Mantikor, version {__version__}'
    logging.info(desc)
    ts = ArgsParser(desc=desc, def_settings_file=None)
    if ts.args.settings:
        # ToDO: add settings flow
        settings = Config(filename=ts.args.settings)

    if ts.args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().handlers[0].setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s [%(funcName)s] - %(message)s'))

    version = Updater(schedule=2)
    if ts.args.version:
        version.check_updates(only_new=False)
        sys.exit(0)
    else:
        version.check_scheduled_updates(schedule=version.schedule)

    torr_server = TorrServer(**{k: v for k, v in vars(ts.parser.parse_args()).items()}, tracker_id='torrserver')

    if ts.args.all:
        ts.parser.set_defaults(rutor=True, nnmclub=True, torrentby=True, kinozal=True, rutracker=True, anidub=True)

    if ts.args.cleanup:
        torr_server.cleanup_torrents(perm=True)

    if ts.args.rutor:
        update_tracker_torrents(tracker=RUTOR, tracker_class=RuTor(proxy=ts.args.proxy), torrserver=torr_server)

    if ts.args.litrcc:
        litrcc_rss_feed_url = f'https://litr.cc/feed/{ts.args.litrcc}/json'
        logging.info(f'litr.cc RSS uuid: {ts.args.litrcc}')
        litrcc = LitrCC(url=litrcc_rss_feed_url)
        torr_server.get_litrcc_torrents()
        for litrcc_item in litrcc.torrents_list:
            torrent_external_url = litrcc_item.get('external_url')
            torrent_title = litrcc_item.get('title')
            torrent_hash = litrcc_item.get('id')
            torrent_poster = litrcc_item.get('image')
            # logging.info(f'Checking: {torrent_title}')
            if torrent_external_url in torr_server.litrcc_torrents_cache:
                # logging.info(f'{torrent_title} will be updated')
                hashes = dict()
                for ts_item in torr_server.litrcc_torrents_list:
                    ts_external_url = ts_item.get('t_url')
                    ts_title = ts_item.get('title')
                    ts_hash = ts_item.get('t_hash')
                    ts_poster = ts_item.get('poster')
                    if torrent_external_url == ts_external_url:
                        hashes[ts_hash] = ts_title
                if torrent_hash and (torrent_hash not in hashes.keys()):
                    logging.info(f'{list(hashes.values())[0]}')
                    logging.info(f'Found update: {torrent_external_url}')
                    indexes = set()
                    data = f'{{"LITRCC":{{"external_url":"{torrent_external_url}"}}}}'
                    for t_hash in hashes.keys():
                        viewed_indexes_list = torr_server.get_torrent_info(t_hash=t_hash)
                        for vi in viewed_indexes_list:
                            indexes.add(vi.get('file_index'))
                    torrserver_torrent = {'link': f'magnet:?xt=urn:btih:{torrent_hash}', 'title': torrent_title,
                                          'poster': torrent_poster, 'save_to_db': True, 'data': data,
                                          'hash': torrent_hash}
                    torr_server.add_updated_torrent(updated_torrent=torrserver_torrent, viewed_episodes=indexes)
                    torr_server.cleanup_torrents(hashes=hashes.keys())
                else:
                    logging.info(f'{torrent_title}')
                    logging.info(f'No new episodes found: {torrent_external_url}')
            else:
                logging.info(f'{torrent_title}')
                logging.info(f'New hash, {torrent_hash}, will be added to the server list')
                data = f'{{"LITRCC":{{"external_url":"{torrent_external_url}"}}}}'
                torrserver_torrent = {'link': f'magnet:?xt=urn:btih:{torrent_hash}', 'title': torrent_title,
                                      'poster': torrent_poster, 'save_to_db': True, 'data': data, 'hash': torrent_hash}
                torr_server.add_torrent(torrent=torrserver_torrent)

    if ts.args.nnmclub:
        update_tracker_torrents(tracker=NNMCLUB, tracker_class=NnmClub(proxy=ts.args.proxy), torrserver=torr_server)

    if ts.args.torrentby:
        update_tracker_torrents(tracker=TORRENTBY, tracker_class=TorrentBy(proxy=ts.args.proxy), torrserver=torr_server)

    if ts.args.kinozal:
        update_tracker_torrents(tracker=KINOZAL,
                                tracker_class=Kinozal(secrets=torr_server.secrets, proxy=ts.args.proxy,
                                                      tracker_id='kinozal_id'), torrserver=torr_server)

    if ts.args.rutracker:
        update_tracker_torrents(tracker=RUTRACKER, tracker_class=Rutracker(proxy=ts.args.proxy), torrserver=torr_server)

    if ts.args.anidub:
        update_tracker_torrents(tracker=ANIDUB, tracker_class=AniDub(proxy=ts.args.proxy), torrserver=torr_server)

    if ts.args.anilibria:
        update_tracker_torrents(tracker=ANILIBRIA, tracker_class=AniLibria(proxy=ts.args.proxy), torrserver=torr_server)


if __name__ == '__main__':
    main()
