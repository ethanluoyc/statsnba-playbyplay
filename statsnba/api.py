# -*- coding: utf-8 -*-
import tempfile
from urllib import (urlencode)
import requests
import functools
import inspect
from requests.exceptions import (HTTPError)
import json


class Api(object):
    """The endpoint for querying the StatsNBA APIs.
        Use this in place of the resource.py
    """

    def __init__(self, cache=False, cache_format='json',
                 transform_json=True):
        self._cache = cache
        self._cache_format = cache_format  # TODO support other format
        self._transform_json = transform_json

    def _CacheResource(self, resource_json):
        # tmp_dir = tempfile.mkdtemp()
        format = self._cache_format
        fd, path = tempfile.mkstemp('.'+format)
        with open(path, 'w') as out_file:
            if format == 'json':
                import json
                json.dump(resource_json, out_file)
            else:
                # TODO csv format
                raise TypeError('the format `{0}` you specified is \
                                not supported'.format(format))

    @staticmethod
    def _TransformResponseDict(resp_dict):
        """Transform the response from stats.nba.com
            The response from stats.nba.com is a JSON object. However,
            for efficiency the fields are not encoded as key-value pairs
            but rather separated as header and rowSets, which is not
            convenient for querying the attributes of the resultSets.
        """
        def _convert_resultset(result_dict):
            result_name = result_dict['name']
            headers = result_dict['headers']
            data = result_dict['rowSet']
            import pandas as pd
            df = pd.DataFrame(data, columns=headers)
            # use this to avoid Mongo conversion error
            return result_name, json.loads(df.to_json(orient='records'))

        from .utils import convert_resultset
        resultSets = map(convert_resultset, resp_dict['resultSets'])
        resp_dict['resultSets'] = {}
        for name, data in resultSets:
            resp_dict['resultSets'][name] = data
        return resp_dict

    def _FetchUrl(self, url, verb='GET'):
        _headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'
                          'AppleWebKit/537.36 (KHTML, like Gecko)'
                          'Chrome/48.0.2564.82 '
                          'Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9'
                      ',image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive'
        }  # Without this header, there will be no err message.
        resp = requests.request(verb, url, headers=_headers)
        try:
            resp.raise_for_status()
        except HTTPError as e:
            # Add a detailed message for why this request failed.
            raise HTTPError(e.message + '\n' + resp.text)
        except Exception as e:
            raise e
        else:
            return resp

    def _BuildUrl(self, base_url, resource, params):
        p = urlencode(params)
        return base_url + resource + '?' + p

    def Resource(resource_name):
        def real_dec(func):
            @functools.wraps(func)
            def fetch_resource(*args, **kwargs):
                called_args = inspect.getcallargs(func, *args, **kwargs)
                # We do not need `self` for building the params
                self = called_args.pop('self')
                url = self._BuildUrl('http://stats.nba.com/stats/',
                                     resource_name,
                                     called_args)
                resp_dict = self._FetchUrl(url).json()
                if self._transform_json:
                    resp_dict = Api._TransformResponseDict(resp_dict)
                if self._cache:
                    self._CacheResource(resp_dict)
                return resp_dict
            return fetch_resource
        return real_dec

    @Resource('playbyplayv2')
    def GetPlayByPlay(self, GameID,
                      EndPeriod=10,
                      StartPeriod=1):
        pass

    @Resource('boxscoretraditionalv2')
    def GetBoxscore(self, GameID,
                    EndPeriod=10,
                    EndRange=14400,
                    RangeType=0,
                    StartPeriod=1,
                    StartRange=0):
        pass

    @Resource('leaguegamelog')
    def GetGamelog(self, Season,
                   SeasonType,
                   Direction='DESC',
                   Sorter=None,
                   Counter=1000,
                   PlayerOrTeam='T',
                   LeagueID='00'):
        pass

    @Resource('leaguedashplayerstats')
    def GetLeaguePlayerStats(self, Season,
                             SeasonType,
                             College='',
                             Conference='',
                             Country='',
                             DateFrom='',
                             DateTo='',
                             Division='',
                             DraftPick='',
                             DraftYear='',
                             GameScope='',
                             GameSegment='',
                             Height='',
                             LastNGames=0,
                             LeagueID='00',
                             Location='',
                             MeasureType='Base',
                             Month=0,
                             OpponentTeamID=0,
                             Outcome='',
                             PORound=0,
                             PaceAdjust='N',
                             PerMode='PerGame',
                             Period=0,
                             PlayerExperience='',
                             PlayerPosition='',
                             PlusMinus='N',
                             Rank='N',
                             SeasonSegment='',
                             ShotClockRange='',
                             StarterBench='',
                             TeamID=0,
                             VsConference='',
                             VsDivision='',
                             Weight=''):
        pass
