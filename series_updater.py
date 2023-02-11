import requests
import os
import json
import logging
import argparse
import yaml
from yarl import URL
from typing import List
from logging.handlers import RotatingFileHandler


__version__ = '0.0.1'


logging.basicConfig(format='%(asctime)s %(levelname)s [%(funcName)s] - %(message)s')
logger = logging.getLogger('parsing_core')


class TorrentsSource(object):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger('_'.join([self.__class__.__name__, __version__]))
        self.add_logger_handler(debug=kwargs.get('debug', False))
        self._server_url = 'http://localhost'

    def add_logger_handler(self, debug=False):
        handlers = ['file']
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

    def _server_request(self, r_type='get', pref='', data=None, timeout=10):
        if data is None:
            data = dict()
        if pref:
            pref = f'/{pref}'
        try:
            if r_type == 'get':
                resp = requests.get(url=f'{self._server_url}{pref}', json=data, timeout=timeout)
            elif r_type == 'post':
                resp = requests.post(url=f'{self._server_url}{pref}', json=data, timeout=timeout)
            else:
                resp = requests.head(url=f'{self._server_url}{pref}', json=data, timeout=timeout)
        except Exception as e:
            self.logger.error(e)
            raise Exception
        return resp


class TorrServer(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = URL(kwargs.get('ts_url'))
        self._server_url: URL = URL.build(scheme=self._server_url.scheme, host=self._server_url.host,
                                          port=kwargs.get('ts_port'))
        self.torrents_list: list = list()
        self.raw = self._get_torrents_list()

    def _get_torrents_list(self):
        resp = self._server_request(r_type='post', pref='torrents', data={'action': 'list'})
        return resp.json()

    def get_torrent_info(self, t_hash):
        resp = self._server_request(r_type='post', pref='viewed', data={'action': 'list', 'hash': t_hash})
        return resp.json()

    def remove_torrent(self, t_hash):
        resp = self._server_request(r_type='post', pref='viewed', data={'action': 'rem', 'hash': t_hash})
        return resp

    def add_torrent(self, torrent):
        data = {'action': 'add'} | torrent
        resp = self._server_request(r_type='post', pref='torrents', data=data)
        return resp

    def set_viewed(self, viewed):
        data = {'action': 'set'} | viewed
        resp = self._server_request(r_type='post', pref='viewed', data=data)
        return resp


class RuTor(TorrentsSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def get_magnet(self):
        pass

    def get_poster(self):
        pass

    @staticmethod
    def is_rutor_link(url):
        if url and ('rutor.info' in url):
            scratches = url.split('/')
            for part in scratches:
                if part.isdecimal():
                    return part
        return None


class LitrCC(TorrentsSource):
    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = URL(url)
        self.torrents_list: list = list()
        self.raw = self._get_torrents_list()

    def _get_torrents_list(self):
        resp = self._server_request(r_type='get')
        return resp.json()

    def check_rutor_url(self):
        pass

    def get_list_of_groups(self):
        pass

    def add_torrent_to_listener(self, secret, group_id):
        pass


class ArgsParser:

    def __init__(self, desc, def_settings_file=None):
        self.parser = argparse.ArgumentParser(description=desc, add_help=True)
        self.parser.add_argument('--settings', action='store', dest='settings', type=str, default=def_settings_file,
                                 help='settings file for future purposes')
        self.parser.add_argument('--ts_url', action='store', dest='ts_url', type=str, default='http://localhost',
                                 help='torrserver url')
        self.parser.add_argument('--ts_port', action='store', dest='ts_port', type=int, default=8090,
                                 help='torrserver port')
        self.parser.add_argument('--litrcc', action='store', dest='litrcc', type=str, default='',
                                 help='feed uuid from litr.cc')
        self.parser.add_argument(
            '--cleanup', action='store_true', dest='cleanup', default=False,
            help='Cleanup mode: merge separate torrents with different episodes for same series to one torrent')
        self.parser.add_argument('--debug', action='store_true', dest='debug', default=False,
                                 help='Enable DEBUG log level')

    @property
    def args(self):
        return self.parser.parse_args()


def main():
    ts = ArgsParser(desc='Awesome series updater for TorrServe', def_settings_file=None)
    torr_server = TorrServer(**{k: v for k, v in vars(ts.parser.parse_args()).items()})

    if ts.args.settings:
        with open(ts.args.settings, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    if ts.args.cleanup:
        # ToDO: add cleanup after update series
        pass

    for i in torr_server.raw:
        t_hash = i.get('hash')
        if t_hash:
            title = i.get('title')
            poster = i.get('poster')
            data = i.get('data')
            try:
                data = json.loads(data)
                t_url = data.get('TSA', dict()).get('srcUrl')
            except Exception as e:
                logger.warning(data)
                logger.warning(e)
                t_url = data
            timestamp = i.get('timestamp')
            t_hash = i.get('hash')
            stat = i.get('stat')
            stat_string = i.get('stat_string')
            torrent_size = i.get('torrent_size')
            torrent = {'title': title, 'poster': poster, 't_url': t_url, 'timestamp': timestamp,
                       't_hash': t_hash, 'stat': stat, 'stat_string': stat_string, 'torrent_size': torrent_size}
            torr_server.torrents_list.append(torrent)
    torr_server.logger.info(f'Torrserver, torrents got: {len(torr_server.torrents_list)}')

    if ts.args.litrcc:
        litr_cc_url = f'https://litr.cc/feed/{ts.args.litrcc}/json'
        litr_cc = LitrCC(url=litr_cc_url, debug=ts.args.debug)
        litr_cc.logger.info(f'Litr.cc mode: RSS uuid: {ts.args.litrcc}')
        for i in litr_cc.raw.get('items', list()):
            t_id = i.get('id')
            if t_id:
                title = i.get('title')
                url = i.get('url')
                date_modified = i.get('date_modified')
                image = i.get('image')
                external_url = i.get('external_url')
                torrent = {'id': str(t_id).lower(), 'title': title, 'url': url, 'date_modified': date_modified,
                           'image': image, 'external_url': external_url}
                litr_cc.torrents_list.append(torrent)
        litr_cc.logger.info(f'Litr.cc mode: torrents got: {len(litr_cc.torrents_list)}')
        for torrent in litr_cc.torrents_list:
            rutor_id = RuTor.is_rutor_link(url=torrent.get('external_url'))
            if rutor_id:
                hashes = list()
                indexes = set()
                for ts_torrent in torr_server.torrents_list:
                    ts_rutor_id = RuTor.is_rutor_link(url=ts_torrent.get('t_url'))
                    if ts_rutor_id:
                        if rutor_id == ts_rutor_id:
                            t_hash = ts_torrent.get('t_hash')
                            hashes.append(t_hash)
                            viewed_indexes_list = torr_server.get_torrent_info(t_hash=t_hash)
                            for vi in viewed_indexes_list:
                                indexes.add(vi.get('file_index'))
                link = torrent.get('id')
                title = torrent.get('title')
                poster = torrent.get('image')
                data = f'{{"TSA":{{"srcUrl":"http://rutor.info/torrent/{rutor_id}"}}}}'
                # data = torrent.get('external_url')
                if link not in hashes:
                    updated_torrent = {'link': f'magnet:?xt=urn:btih:{link}', 'title': title, 'poster': poster,
                                       'save_to_db': True, 'data': data}
                    res = torr_server.add_torrent(torrent=updated_torrent)
                    if res.status_code == 200:
                        torr_server.logger.info(f'{title} => added/updated')
                    for idx in indexes:
                        viewed = {'hash': link, 'file_index': idx}
                        res = torr_server.set_viewed(viewed=viewed)
                        if res.status_code == 200:
                            torr_server.logger.info(f'{idx} episode => set as viewed')
            else:
                pass  # catch non-rutor torrent


if __name__ == '__main__':
    main()
