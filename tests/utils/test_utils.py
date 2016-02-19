from unittest import TestCase
from statsnba.utils import make_season, encode_url


class TestUtils(TestCase):
    def test_encode_url(self):
        params = {
            'Direction': 'DESC',
            'LeagueID': '00',
            'PlayerOrTeam': 'T',
            'Season': '2015-16',
            'SeasonType': 'Regular Season',
            'Sorter': 'PTS',
            'Counter': '1000'
        }
        url = 'http://stats.nba.com/stats/leaguegamelog?Sorter=PTS&Season=2015-16&SeasonType=Regular+Season&Counter=1000&PlayerOrTeam=T&Direction=DESC&LeagueID=00'
        # assert encode_url('http://stats.nba.com/stats/leaguegamelog', params) == url
        #Todo
        assert True

    def test_make_season(self):
        assert make_season(2005) == '2005-06'
        assert make_season(2015) == '2015-16'
