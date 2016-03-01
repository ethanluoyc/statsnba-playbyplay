import scrapy
import urllib
from crawl.items import StatsnbaItem
import json


class NBABaseSpider(scrapy.Spider):
    base_url = 'http://stats.nba.com/stats/'
    resource = 'base'
    allowed_domains = ['stats.nba.com']
    default_params = {}  # to be implemented in children classes

    def __init__(self):
        super(NBABaseSpider, self).__init__()
        self.start_urls = []

    def parse(self, response):
        if response.status != 200:
            self.logger.error('downloading failed: %s, error_code: %s', response.url, response.status)
            yield
        result_dict = json.loads(response.body)
        resultSets = map(NBABaseSpider._convert_result, result_dict['resultSets'])
        # TODO may refactor this into pipeline
        result_dict['resultSets'] = {}
        for name, data in resultSets:
            result_dict['resultSets'][name] = data
        self.logger.info('parse called on resource %s', response.url)

        yield StatsnbaItem(result_dict)


    @staticmethod
    def _convert_result(result_dict):
        """
            :param result_dict the dict containing the headers, name and rowSet (see sample_data)
            :return (name, data) a tuple containing the name of the resultSet and data
        """
        result_name = result_dict['name']
        headers = result_dict['headers']
        data = result_dict['rowSet']
        import pandas as pd
        df = pd.DataFrame(data, columns=headers)
        # use this to avoid Mongo conversion error
        return result_name, json.loads(df.to_json(orient='records'))

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
