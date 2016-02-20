from os import path
from unittest import TestCase
from statsnba.utils import make_season, encode_url, make_table

SAMPLEDATA_DIR = path.join(path.dirname(__file__), '../sample_data/')


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

    def test_make_table(self):
        params = {
            'Direction': 'DESC',
            'LeagueID': '00',
            'PlayerOrTeam': 'T',
            'Season': '2015-16',
            'SeasonType': 'Regular Season',
            'Sorter': 'PTS',
            'Counter': '1000'
        }

        import json
        with open(path.join(SAMPLEDATA_DIR, 'leaguegamelog.json'), 'r') as f:
            json_data = json.load(f)
            df = make_table(json_data)
            records = json.loads(df.to_json(orient='records'))

            assert records[0]['GAME_ID'] == '0021500391'
            for k, v in params.items():
                assert str(records[0][k]) == str(params[k])
