from os import path
import pytest
import json
from statsnba.parse_game import Game, Player

SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


# sample game id is "0020901030"
# http://stats.nba.com/game/#!/0020901030/ for online view

@pytest.fixture
def boxscore_data():
    return json.load(open(path.join(SAMPLEDATA_DIR, 'sample_boxscore.json'), 'r'))


@pytest.fixture
def pbp_data():
    return json.load(open(path.join(SAMPLEDATA_DIR, 'sample_playbyplay.json'), 'r'))


def test_game_creation(boxscore_data, pbp_data):
    game = Game(boxscore_data, pbp_data)
    assert game.home_team == 'MIA'
    assert game.away_team == 'CHA'

    tyson = Player({
        "TO": 3.0,
        "MIN": "33:12",
        "PLAYER_ID": 2199,
        "TEAM_ID": 1610612766,
        "REB": 11.0,
        "COMMENT": "",
        "FG3A": 0.0,
        "PLAYER_NAME": "Tyson Chandler",
        "AST": 0.0,
        "TEAM_ABBREVIATION": "CHA",
        "FG3M": 0.0,
        "OREB": 2.0,
        "FGM": 1.0,
        "START_POSITION": "",
        "PF": 3.0,
        "PTS": 4.0,
        "FGA": 3.0,
        "PLUS_MINUS": 12.0,
        "STL": 2.0,
        "FTA": 2.0,
        "BLK": 3.0,
        "GAME_ID": "0020901030",
        "DREB": 9.0,
        "FTM": 2.0,
        "FT_PCT": 1.0,
        "FG_PCT": 0.333,
        "FG3_PCT": 0.0,
        "TEAM_CITY": "Charlotte"
    })

    assert len(game.away_starters) == 5

    # Check if player satisfies some conditions
    assert tyson.team_abbr == 'CHA'
    assert tyson not in game.away_starters
    assert tyson in game.away_bench
    assert tyson not in game.home_bench
    assert tyson not in game.home_starters


def test_game_playbyplay(boxscore_data, pbp_data):
    game = Game(boxscore_data, pbp_data)
    assert game.playbyplay[43][1].remaining_time == '4:22'
    assert game.playbyplay[43] == game.playbyplay[42]


def test_game_compute_stats():
    pytest.xfail()
