#!/usr/bin/python3
# -*- coding: utf-8 -*-
# coding: utf8

"""
Copyright: (c) 2023, Streltsov Sergey, straltsou.siarhei@gmail.com
init release 2023-02-13
Tests for TorrentsSource
"""


import pytest
import requests
# import requests_mock
from series_updater import TorrentsSource
from requests import HTTPError


def test_server_request_post_ok(requests_mock):
    requests_mock.post('http://localhost/test_post', json={'test': 'ok', 'code': 200})
    ts_obj = TorrentsSource(server_url='http://localhost')
    resp = ts_obj._server_request(r_type='post', pref='test_post', data={'action': 'test'})
    assert {'test': 'ok', 'code': 200} == resp.json()


def test_server_request_get_ok(requests_mock):
    requests_mock.get('http://localhost/test_get', json={'test': 'ok', 'code': 200})
    ts_obj = TorrentsSource(server_url='http://localhost')
    resp = ts_obj._server_request(r_type='get', pref='test_get')
    assert {'test': 'ok', 'code': 200} == resp.json()
