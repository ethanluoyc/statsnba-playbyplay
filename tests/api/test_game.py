import pytest
from os import path
from statsnba.api.gamelogs import LeagueGameLog
import json

SAMPLEDATA_DIR = path.join(path.dirname(__file__), '../sample_data/')


def test_to_records():
    with open(path.join(SAMPLEDATA_DIR, 'playbyplay.json'), 'r') as f:
        params = {
            "Direction": "DESC",
            "Sorter": "PTS",
            "Counter": 1000,
            "PlayerOrTeam": "T",
            "SeasonType": "Regular Season",
            "Season": "2015-16",
            "LeagueID": "00"
        }
        log = LeagueGameLog(params=params)
        game = log.to_records()[0]
        assert game['GAME_ID'] == '0021500391'
