from os import path
import pytest
import mock
import httpretty

from models.nba import NBAEvent
from statsnba.models.base import Game, Player
from statsnba.models.nba import NBAGame, NBAPlayer


SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')

# sample game id is "0020901030"
# http://stats.nba.com/game/#!/0020901030/ for online view
def read_json(file_path):
    import json
    f = open(path.join(SAMPLEDATA_DIR, file_path), 'r')
    data = json.load(f)
    f.close()
    return data


@pytest.fixture
def sample_data(request):
    httpretty.enable()
    httpretty.register_uri(httpretty.GET, 'http://stats.nba.com/stats/boxscoretraditionalv2?StartRange=7210&GameID=0020901030&EndPeriod=10&RangeType=2&StartPeriod=1&EndRange=8020',
                           body=read_json('../resources/boxscoretraditionalv2%3fStartRange=7210&GameID=0020901030&EndPeriod=10&RangeType=2&StartPeriod=1&EndRange=8020'),
                           match_querystring=True)
    httpretty.register_uri(httpretty.GET, 'http://stats.nba.com/stats/boxscoretraditionalv2?StartRange=14410&GameID=0020901030&EndPeriod=10&RangeType=2&StartPeriod=1&EndRange=17970',
                           body='../resources/boxscoretraditionalv2%3fStartRange=14410&GameID=0020901030&EndPeriod=10&RangeType=2&StartPeriod=1&EndRange=17970',
                           match_querystring=True)
    httpretty.register_uri(httpretty.GET, 'http://stats.nba.com/stats/boxscoretraditionalv2?StartRange=21610&GameID=0020901030&EndPeriod=10&RangeType=2&StartPeriod=1&EndRange=23140',
                           body='../resources/boxscoretraditionalv2%3fStartRange=21610&GameID=0020901030&EndPeriod=10&RangeType=2&StartPeriod=1&EndRange=23140',
                           match_querystring=True)

    def fin():
        httpretty.disable()

    request.addFinalizer(fin)


@pytest.fixture(scope='module')
def sample_playbyplay():
    return read_json('sample_boxscore')


@pytest.fixture(scope='module')
def sample_boxscore():
    return read_json('sample_playbyplay')


@mock.patch('statsnba.models.nba.FsLoader', autospec=True)
@pytest.fixture(scope='module')
def sample_game(mock_fsloader):
    # http://stackoverflow.com/questions/9728748/mocking-a-class-method-that-is-used-via-an-instance
    mock_fsloader().get_boxscore.return_value = read_json('sample_boxscore.json')
    mock_fsloader().get_playbyplay.return_value = read_json('sample_playbyplay.json')
    game = Game(game_id='0020901030')
    return game


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
    first_event = NBAEvent({
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
    assert sample_game.playbyplay[0].players == sample_game.playbyplay[0].players
    assert sample_game.playbyplay[0].players == sample_game.playbyplay[1].players
    assert sample_game.playbyplay[0].players != sample_game.playbyplay[45].players
    assert sample_game.playbyplay[45].players != sample_game.playbyplay[46].players
    assert len(sample_game.playbyplay) == 450


def test_parse_event():
    sample_event = {
                "HOMEDESCRIPTION": None,
                "PLAYER2_TEAM_CITY": None,
                "SCOREMARGIN": None,
                "PLAYER3_TEAM_ABBREVIATION": None,
                "PLAYER1_NAME": "Tyson Chandler",
                "PCTIMESTRING": "10:44",
                "PLAYER1_TEAM_ID": 1.610612766e+09,
                "PLAYER1_TEAM_CITY": "Charlotte",
                "PLAYER2_NAME": None,
                "PLAYER1_ID": 2199,
                "PERSON3TYPE": 0,
                "WCTIMESTRING": "8:09 PM",
                "GAME_ID": "0020901030",
                "PERSON1TYPE": 5,
                "EVENTMSGTYPE": 4,
                "EVENTNUM": 113,
                "PLAYER3_TEAM_NICKNAME": None,
                "PLAYER1_TEAM_ABBREVIATION": "CHA",
                "PERIOD": 2,
                "NEUTRALDESCRIPTION": None,
                "PLAYER2_TEAM_ABBREVIATION": None,
                "EVENTMSGACTIONTYPE": 0,
                "PLAYER2_TEAM_NICKNAME": None,
                "PLAYER3_NAME": None,
                "PLAYER3_ID": 0,
                "SCORE": None,
                "PLAYER3_TEAM_ID": None,
                "PLAYER3_TEAM_CITY": None,
                "PLAYER1_TEAM_NICKNAME": "Bobcats",
                "VISITORDESCRIPTION": "Chandler REBOUND (Off:1 Def:4)",
                "PLAYER2_TEAM_ID": None,
                "PLAYER2_ID": 0,
                "PERSON2TYPE": 0
            }

    event = NBAEvent(sample_event)
    from datetime import timedelta
    assert event.period_elapsed_time == timedelta(minutes=1, seconds=16)
    assert event.period_elapsed_time.seconds == 76
    assert event.overall_elapsed_time == timedelta(minutes=12+1, seconds=16)
    assert event.overall_elapsed_time.seconds == 796

    sample_overtime_event = {
                "HOMEDESCRIPTION": None,
                "PLAYER2_TEAM_CITY": None,
                "SCOREMARGIN": None,
                "PLAYER3_TEAM_ABBREVIATION": None,
                "PLAYER1_NAME": "Tyson Chandler",
                "PCTIMESTRING": "4:44",
                "PLAYER1_TEAM_ID": 1.610612766e+09,
                "PLAYER1_TEAM_CITY": "Charlotte",
                "PLAYER2_NAME": None,
                "PLAYER1_ID": 2199,
                "PERSON3TYPE": 0,
                "WCTIMESTRING": "8:09 PM",
                "GAME_ID": "0020901030",
                "PERSON1TYPE": 5,
                "EVENTMSGTYPE": 4,
                "EVENTNUM": 113,
                "PLAYER3_TEAM_NICKNAME": None,
                "PLAYER1_TEAM_ABBREVIATION": "CHA",
                "PERIOD": 6,
                "NEUTRALDESCRIPTION": None,
                "PLAYER2_TEAM_ABBREVIATION": None,
                "EVENTMSGACTIONTYPE": 0,
                "PLAYER2_TEAM_NICKNAME": None,
                "PLAYER3_NAME": None,
                "PLAYER3_ID": 0,
                "SCORE": None,
                "PLAYER3_TEAM_ID": None,
                "PLAYER3_TEAM_CITY": None,
                "PLAYER1_TEAM_NICKNAME": "Bobcats",
                "VISITORDESCRIPTION": "Chandler REBOUND (Off:1 Def:4)",
                "PLAYER2_TEAM_ID": None,
                "PLAYER2_ID": 0,
                "PERSON2TYPE": 0
            }

    event = NBAEvent(sample_overtime_event)
    assert event.period_elapsed_time == timedelta(seconds=16)
    assert event.overall_elapsed_time == timedelta(minutes=48 + 5, seconds=16)


def test_pbp_lineups(sample_game):
    assert len(sample_game.lineups) == 32
