import pytest
from statsnba.api.boxscore import BoxscoreTraditional
from statsnba.utils import make_table


class TestBoxscore:

    #  Sample data may be found in tests/sample_data/boxscore.json
    default_params = {
        'EndPeriod': '10',
        'EndRange': '14400',
        'GameID': '0021500818',
        'RangeType': '0',
        'Season': '2015-16',
        'SeasonType': 'Regular Season',
        'StartPeriod': '1',
        'StartRange': '0'
    }

    def test_data(self):
        boxscore = BoxscoreTraditional(params=TestBoxscore.default_params)
        jd = boxscore.data[0]
        jd = make_table(jd)
        import json
        jd = json.loads(jd.to_json(orient='records'))
        first_row = jd[0]
        assert first_row['GAME_ID'] == '0021500818'
        assert first_row['TEAM_ID'] == 1610612759 # TODO may assert all fields

