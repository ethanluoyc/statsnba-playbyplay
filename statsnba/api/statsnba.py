# -*- coding: utf-8 -*-
import urllib
from fetcher import Fetcher


class StatsNBAAPI(object):
    base_url = 'http://stats.nba.com/stats/'
    resource = None
    default_params = {}

    def __init__(self, params, fetcher=None, collection=None):
        if type(params) is not list:
            params = [params]
        self.params = params

        self.collection = collection

        updated_params = []
        for p in self.params:
            self._validate_params(p)
            updated_params.append(self._update_params(p))

        self.params = updated_params

        urls = []
        for p in self.params:
            urls.append(type(self)._encode_url(p))

        if fetcher is None:
            self.fetcher = Fetcher(api=self)

        self.fetcher.fetch(urls)  # start fetching with grequests
        self.fetcher.get()

    @classmethod
    def _update_params(cls, params):
        params_copy = cls.default_params.copy()
        params_copy.update(params)
        return params_copy

    @classmethod
    def _encode_url(cls, params):
        p = urllib.urlencode(params)
        return cls.base_url + cls.resource + '?' + p

    @classmethod
    def _validate_params(cls, params):
        if not cls.default_params:
            return True
        for k, v in params.items():
            try:
                cls.default_params[k]
            except KeyError:
                raise Exception('parameter {k} should not be used!'.format(k=k))
        return True

    def post_download(self, response):
        """
            :param response a response object from requests
        """
        self.collection.insert_one(response.json())
