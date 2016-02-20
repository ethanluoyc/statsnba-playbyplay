# -*- coding: utf-8 -*-
import urllib.parse

from statsnba.fetcher import Fetcher


class StatsNBAAPI(object):
    base_url = 'http://stats.nba.com/stats/'
    default_parameters = {}

    def __init__(self, params, fetcher=None):
        if fetcher is None:
            self.fetcher = Fetcher()

        if type(params) is not list:
            params = [params]
        self.params = params


    def _encode_url(self, resource, params):
        p = urllib.parse.urlencode(params)
        return StatsNBAAPI.base_url + resource + '?' + p
