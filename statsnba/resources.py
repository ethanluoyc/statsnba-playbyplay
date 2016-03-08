import json
import urllib
import logging

logger = logging.getLogger(__name__)


class StatsNBA(object):
    base_url = 'http://stats.nba.com/stats/'
    allowed_domains = ['stats.nba.com']
    default_params = dict()
    resource = ''

    @classmethod
    def fetch_resource(cls, params):
        params = cls._update_params(params)
        url = cls._encode_url(params)
        import requests
        from crawl.settings import DEFAULT_REQUEST_HEADERS
        response = requests.get(url, headers=DEFAULT_REQUEST_HEADERS)
        resource = cls._parse_response(response)
        return resource

    @classmethod
    def _parse_response(cls, response):
        if response.status_code != 200:
            logger.error('downloading failed: %s, error_code: %s', response.url, response.status_code)
        result_dict = json.loads(response.text)
        resultSets = map(StatsNBA._convert_result, result_dict['resultSets'])
        # TODO may refactor this into pipeline
        result_dict['resultSets'] = {}
        for name, data in resultSets:
            result_dict['resultSets'][name] = data
        logger.info('parse called on resource %s', response.url)
        return result_dict

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


class StatsNBABoxscore(StatsNBA):
    resource = 'boxscoretraditionalv2'
    name = 'boxscoretraditional'
    default_params = {
        'EndPeriod': '10',
        'EndRange': '14400',
        'GameID': None,
        'RangeType': '0',
        'StartPeriod': '1',
        'StartRange': '0'
    }

    @classmethod
    def find_boxscore_in_range(cls, game_id, start_range, end_range):
        return cls.fetch_resource({'GameID': game_id,
                                   'StartRange': start_range,
                                   'EndRange': end_range,
                                   'RangeType': '2'
                                })


class StatsNBAGamelog(StatsNBA):
    resource = 'leaguegamelog'
    name = 'gamelog'
    default_params = {
        "Direction": "DESC",
        "Sorter": "PTS",
        "Counter": 1000,
        "PlayerOrTeam": "T",
        "SeasonType": "Regular Season",
        "Season": None,
        "LeagueID": "00"
    }


class StatsNBAPlayByPlay(StatsNBA):
    resource = 'playbyplay'
    default_params = {
        'EndPeriod': '10',
        'GameID': None,
        'StartPeriod': '1'
    }
