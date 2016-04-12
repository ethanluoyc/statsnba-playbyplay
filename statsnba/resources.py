import json
import urllib
import logging

logger = logging.getLogger(__name__)


class StatsNBA(object):
    base_url = 'http://stats.nba.com/stats/'
    allowed_domains = ['stats.nba.com']
    default_params = dict()
    resource = ''

    def __init__(self, data):
        self._data = data

    @classmethod
    def fetch_resource(cls, params):
        params = cls._update_params(params)
        url = cls._encode_url(params)
        import requests
        logger.debug('Fetching {}...'.format(url))
        response = requests.get(url, headers={
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)' \
                          ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 ' \
                          'Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9' \
                      ',image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive'
        })
        if response.status_code != 200:
            raise Exception(url)
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

        import sys
        if hasattr(sys, '_called_from_test'):
            cls._cache_resource(result_dict)

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

    @classmethod
    def _cache_resource(cls, resource):
        pass


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

    HOME_IDX = 0
    AWAY_IDX = 1

    @classmethod
    def find_boxscore_in_range(cls, game_id, start_range, end_range):
        return cls.fetch_resource({'GameID': game_id,
                                   'StartRange': start_range,
                                   'EndRange': end_range,
                                   'RangeType': '2'
                                })

    @classmethod
    def _cache_resource(cls, resource):
        import pandas as pd
        import os, tempfile
        tmp_dir = tempfile.mkdtemp()
        game_id = resource['parameters']['GameID']
        pd.DataFrame(resource['resultSets']['TeamStats']).to_csv(os.path.join(tmp_dir, '%s_%s.csv' % (cls.__name__, game_id)))

    @classmethod
    def home_boxscore(cls, data):
        return data['resultSets']['TeamStats'][cls.HOME_IDX]

    @classmethod
    def away_boxscore(cls, data):
        return data['resultSets']['TeamStats'][cls.AWAY_IDX]

    @classmethod
    def player_stats(cls, data):
        return data['resultSets']['PlayerStats']


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
    resource = 'playbyplayv2'
    default_params = {
        'EndPeriod': '10',
        'GameID': None,
        'StartPeriod': '1'
    }

    @classmethod
    def _cache_resource(cls, resource):
        import pandas as pd
        import os, tempfile
        tmp_dir = tempfile.mkdtemp()
        game_id = resource['parameters']['GameID']
        pd.DataFrame(resource['resultSets']['PlayByPlay']).to_csv(os.path.join(tmp_dir, '%s_%s.csv' % (cls.__name__, game_id)))


class StatsNBALeaguePlayerStats(StatsNBA):
    resource = 'leaguedashplayerstats'
    default_params = {
        'College': '',
        'Conference': '',
        'Country': '',
        'DateFrom': '',
        'DateTo': '',
        'Division': '',
        'DraftPick': '',
        'DraftYear': '',
        'GameScope': '',
        'GameSegment': '',
        'Height': '',
        'LastNGames': 0,
        'LeagueID': '00',
        'Location': '',
        'MeasureType': 'Base',
        'Month': 0,
        'OpponentTeamID': 0,
        'Outcome': '',
        'PORound': 0,
        'PaceAdjust': 'N',
        'PerMode': 'PerGame',
        'Period': 0,
        'PlayerExperience': '',
        'PlayerPosition': '',
        'PlusMinus': 'N',
        'Rank': 'N',
        'Season': None,
        'SeasonSegment': '',
        'SeasonType': 'Regular Season',
        'ShotClockRange': '',
        'StarterBench': '',
        'TeamID': 0,
        'VsConference': '',
        'VsDivision': '',
        'Weight': ''
    }
