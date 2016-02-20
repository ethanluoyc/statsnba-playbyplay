# -*- coding: utf-8 -*-
import urllib.parse

from statsnba.fetcher import Fetcher


class StatsNBAAPI(object):
    base_url = 'http://stats.nba.com/stats/'
    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'\
        ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 '\
        'Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9'\
        ',image/webp,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive'
    }

    def __init__(self, params, fetcher=None):
        if fetcher is None:
            self.fetcher = Fetcher()
        if type(params) is not list:
            params = [params]
        self.params = params

    def _encode_url(self, resource, params):
        p = urllib.parse.urlencode(params)
        return StatsNBAAPI.base_url + resource + '?' + p
