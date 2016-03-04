from os import path
import pytest

from models.mongo import MongoEvent
from statsnba.models.factory import Game, Player

SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


# sample game id is "0020901030"
# http://stats.nba.com/game/#!/0020901030/ for online view
@pytest.fixture(scope='module')
def sample_game():
    game = Game(backend='mongo', game_id='0020901030')
    return game

@pytest.fixture(scope='module')
def tyson():
    pass


def test_game_creation(sample_game):
    assert sample_game.home_team == 'MIA'
    assert sample_game.away_team == 'CHA'

    tyson = Player(player_stats={
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

    assert len(sample_game.away_starters) == 5

    # Check if player satisfies some conditions
    assert tyson.team_abbr == 'CHA'
    assert tyson not in sample_game.away_starters
    assert tyson in sample_game.away_bench
    assert tyson not in sample_game.home_bench
    assert tyson not in sample_game.home_starters


def test_game_playbyplay(sample_game):
    first_event = MongoEvent({
                "HOMEDESCRIPTION": None,
                "PLAYER2_TEAM_CITY": None,
                "SCOREMARGIN": None,
                "PLAYER3_TEAM_ABBREVIATION": None,
                "PLAYER1_NAME": None,
                "PCTIMESTRING": "12:00",
                "PLAYER1_TEAM_ID": None,
                "PLAYER1_TEAM_CITY": None,
                "PLAYER2_NAME": None,
                "PLAYER1_ID": 0,
                "PERSON3TYPE": 0,
                "WCTIMESTRING": "7:41 PM",
                "GAME_ID": "0020901030",
                "PERSON1TYPE": 0,
                "EVENTMSGTYPE": 12,
                "EVENTNUM": 0,
                "PLAYER3_TEAM_NICKNAME": None,
                "PLAYER1_TEAM_ABBREVIATION": None,
                "PERIOD": 1,
                "NEUTRALDESCRIPTION": None,
                "PLAYER2_TEAM_ABBREVIATION": None,
                "EVENTMSGACTIONTYPE": 0,
                "PLAYER2_TEAM_NICKNAME": None,
                "PLAYER3_NAME": None,
                "PLAYER3_ID": 0,
                "SCORE": None,
                "PLAYER3_TEAM_ID": None,
                "PLAYER3_TEAM_CITY": None,
                "PLAYER1_TEAM_NICKNAME": None,
                "VISITORDESCRIPTION": None,
                "PLAYER2_TEAM_ID": None,
                "PLAYER2_ID": 0,
                "PERSON2TYPE": 0
            })

    assert sample_game.playbyplay[0] == first_event
    assert len(sample_game.playbyplay) == 450

def test_pbp_lineups(sample_game):
    assert len(sample_game.lineups) == 25

def test_fetch_period(sample_game):
    params = sample_game._boxscore['parameters'].copy()
    params.update({
        'StartRange': '7201',
        'EndRange': '8020',
        'RangeType': '2',
        'GameID': str(params['GameID'])
    })
    from crawl.settings import DEFAULT_REQUEST_HEADERS

    import requests
    from crawl.spiders.basespider import NBABaseSpider
    r = requests.get('http://stats.nba.com/stats/boxscoretraditionalv2', params=params, headers=DEFAULT_REQUEST_HEADERS)
    result_sets = map(NBABaseSpider._convert_result, r.json()['resultSets'])
    assert result_sets is list
    assert len(result_sets['PlayerStats']) == 10
