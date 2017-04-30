# -*- coding: utf-8 -*-
import tempfile
from urllib.parse import (urlencode)
import requests
import requests_cache
import functools
import inspect
from requests.exceptions import (HTTPError)


# Without this header, there will be no err message.
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
    'Connection': 'keep-alive'}


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
            resp = self._FetchUrl(url)
            resp_dict = resp.json()
            if self._transform_json:
                resp_dict = Api._TransformResponseDict(resp_dict)
            return resp_dict
        return fetch_resource
    return real_dec


# noinspection PyPep8Naming
class Api(object):
    """The endpoint for querying the StatsNBA APIs.
        Use this in place of the resource.py

    When you want to query some data from stats.nba.com, the way you would do
    it would be to first instantiate an Api object. like so:

    >>> api = Api()

    Then you can use the public methods on the object to perform the queries.

    Notice that however, if you are interested in fetching statistics about a
    particular game, you may not need to use this class directly except for one
    purpose: fetch a list of game ids using this api. Other than that, the most
    convenient way to get information about a particular object is to use the
    Game object.
    """

    def __init__(self, cache=False,
                 cache_filename="requests.cache"):
        self._cache = cache
        if cache:
            requests_cache.install_cache(cache_filename)
        self._transform_json = True

    @staticmethod
    def _TransformResponseDict(resp_dict):
        """Transform the response from stats.nba.com
            The response from stats.nba.com is a JSON object. However,
            for efficiency the fields are not encoded as key-value pairs
            but rather separated as header and rowSets, which is not
            convenient for querying the attributes of the resultSets.
        """

        from .utils import convert_resultset
        resultSets = map(convert_resultset, resp_dict['resultSets'])
        resp_dict['resultSets'] = {}
        for name, data in resultSets:
            resp_dict['resultSets'][name] = data
        return resp_dict

    def _FetchUrl(self, url, verb='GET'):
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

    @staticmethod
    def _BuildUrl(base_url, resource, params):
        p = urlencode(params)
        return base_url + resource + '?' + p

    # The below functions are API endpoints.
    @Resource('playbyplayv2')
    def GetPlayByPlay(self, GameID,
                      EndPeriod=10,
                      StartPeriod=1):
        """Download the PlayByPlay"""
        pass

    @Resource('boxscoretraditionalv2')
    def GetBoxscore(self, GameID,
                    EndPeriod=10,
                    EndRange=14400,
                    RangeType=0,
                    StartPeriod=1,
                    StartRange=0):
        """Download the boxscore"""
        pass

    @Resource('leaguegamelog')
    def GetGamelog(self, Season,
                   SeasonType,
                   Direction='DESC',
                   Sorter="DATE",
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

    def GetSeasonGameIDs(self, Season,
                         SeasonType, **kwargs):
        """Get a list of the game_ids from the SeasonType of Season"""
        gamelog = self.GetGamelog(Season, SeasonType, **kwargs)
        return list(set([l['GAME_ID'] for l in gamelog['resultSets']['LeagueGameLog']]))

    def GetPlayerStats(self, PlayerID):
        pass  # TODO

    @Resource('boxscoresummaryv2')
    def GetBoxscoreSummary(self, GameID):
        pass

__all__ = ['Api']
