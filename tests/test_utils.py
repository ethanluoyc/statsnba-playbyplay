from os import path
import pytest
from statsnba.utils import make_season, convert_resultset

SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


@pytest.fixture()
def gamelog_data(request):
    sample_data = open(path.join(SAMPLEDATA_DIR, 'leaguegamelog.json'), 'r')
    return sample_data


def test_make_season():
    assert make_season(2005) == '2005-06'
    assert make_season(2015) == '2015-16'


def test_convert_result(gamelog_data):
    import json
    gamelog_json = json.load(gamelog_data)
    name, data = convert_resultset(gamelog_json['resultSets'][0])
    assert name == 'LeagueGameLog'
    assert type(data) is list
    assert type(data[0]) is dict
    # TODO finish other assertions
