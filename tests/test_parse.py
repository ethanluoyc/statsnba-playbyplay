from os import path
import pytest
from statsnba.models.nba import NBAEvent

SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


@pytest.fixture()
def event():
    pass


def test_parse():
    import pandas as pd
    records = pd.read_csv(path.join(SAMPLEDATA_DIR, 'events.csv')).to_dict(orient='records')
    assert records[0]['EVENTMSGTYPE'] == 1
    event = NBAEvent(records[0])
    assert event.event_type == 'shot made'
    assert event.converted_y is None
    assert event.player == 'Ty Lawson'


def test_parse_result():
    event = {
        "Unnamed: 0": 54,
        "EVENTMSGTYPE": 2,
        "EVENTMSGACTIONTYPE": 1,
        "EVENTNUM": 2,
        "GAME_ID": 21000782,
        "HOMEDESCRIPTION": None,
        "NEUTRALDESCRIPTION": None,
        "PCTIMESTRING": "11:36",
        "PERIOD": 1,
        "PERSON1TYPE": 5.0,
        "PERSON2TYPE": 0,
        "PERSON3TYPE": 0,
        "PLAYER1_ID": 2546,
        "PLAYER1_NAME": "Carmelo Anthony",
        "PLAYER1_TEAM_ABBREVIATION": "DEN",
        "PLAYER1_TEAM_CITY": "Denver",
        "PLAYER1_TEAM_ID": 1610612743,
        "PLAYER1_TEAM_NICKNAME": "Nuggets",
        "PLAYER2_ID": 0,
        "PLAYER2_NAME": None,
        "PLAYER2_TEAM_ABBREVIATION": None,
        "PLAYER2_TEAM_CITY": None,
        "PLAYER2_TEAM_ID": None,
        "PLAYER2_TEAM_NICKNAME": None,
        "PLAYER3_ID": 0,
        "PLAYER3_NAME": None,
        "PLAYER3_TEAM_ABBREVIATION": None,
        "PLAYER3_TEAM_CITY": None,
        "PLAYER3_TEAM_ID": 1610612744,
        "PLAYER3_TEAM_NICKNAME": None,
        "SCORE": None,
        "SCOREMARGIN": None,
        "VISITORDESCRIPTION": "MISS Anthony 16' Jump Shot",
        "WCTIMESTRING": "10:52 PM"
    }
    parsed = NBAEvent(event)
    assert parsed.result == 'missed'

    event['EVENTMSGTYPE'] = 1
    event['VISITORDESCRIPTION'] = "Anthony 16' Jump Shot"
    parsed = NBAEvent(event)
    assert parsed.result == 'made'


def test_parse_num_outof():
    event = {
        "Unnamed: 0": 109,
        "EVENTMSGTYPE": 3,
        "EVENTMSGACTIONTYPE": 10,
        "EVENTNUM": 30,
        "GAME_ID": 21000782,
        "HOMEDESCRIPTION": None,
        "NEUTRALDESCRIPTION": None,
        "PCTIMESTRING": "8:20",
        "PERIOD": 1,
        "PERSON1TYPE": 5.0,
        "PERSON2TYPE": 0,
        "PERSON3TYPE": 0,
        "PLAYER1_ID": 2403,
        "PLAYER1_NAME": "Nene",
        "PLAYER1_TEAM_ABBREVIATION": "DEN",
        "PLAYER1_TEAM_CITY": "Denver",
        "PLAYER1_TEAM_ID": 1610612743.0,
        "PLAYER1_TEAM_NICKNAME": "Nuggets",
        "PLAYER2_ID": 0,
        "PLAYER2_NAME": None,
        "PLAYER2_TEAM_ABBREVIATION": None,
        "PLAYER2_TEAM_CITY": None,
        "PLAYER2_TEAM_ID": None,
        "PLAYER2_TEAM_NICKNAME": None,
        "PLAYER3_ID": 0,
        "PLAYER3_NAME": None,
        "PLAYER3_TEAM_ABBREVIATION": None,
        "PLAYER3_TEAM_CITY": None,
        "PLAYER3_TEAM_ID": None,
        "PLAYER3_TEAM_NICKNAME": None,
        "SCORE": "7 - 4",
        "SCOREMARGIN": "-3",
        "VISITORDESCRIPTION": "Nene Free Throw 1 of 1 (3 PTS)",
        "WCTIMESTRING": "10:56 PM"
    }
    parsed = NBAEvent(event)
    assert parsed.num == '1'
    assert parsed.outof == '1'


def test_parse_score():
    event = {
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
            }
    parsed = NBAEvent(event)

    assert parsed.home_score is None

    assert parsed.away_score is None

    event['SCORE'] = "8 - 15"
    parsed = NBAEvent(event)
    assert parsed.home_score == '8'
    assert parsed.away_score == '15'


def test_parse_unidentified():
    pytest.fail()
