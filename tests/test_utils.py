from os import path
import pytest
from statsnba.utils import make_season, make_table, convert_result

SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


@pytest.fixture()
def gamelog_data(request):
    sample_data = open(path.join(SAMPLEDATA_DIR, 'leaguegamelog.json'), 'r')
    return sample_data

def test_make_season():
    assert make_season(2005) == '2005-06'
    assert make_season(2015) == '2015-16'


def test_make_table():
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


def test_convert_result(gamelog_data):
    import json
    gamelog_json = json.load(gamelog_data)
    name, data = convert_result(gamelog_json['resultSets'][0])
    assert name == 'LeagueGameLog'
    assert type(data) is list
    assert type(data[0]) is dict
    # TODO finish other assertions
