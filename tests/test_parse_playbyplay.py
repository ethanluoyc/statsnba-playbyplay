"""
    This tests generating a sample game playbyplay
    The game selected has GameID='0020901030'
    It is the game in 2009-10, CHARLOTTE BOBCATS Vs. MIAMI HEAT
    Visit
        http://stats.nba.com/game/#!/0020901030/
    for details of this game.

    Boxscore queries URL:
    http://stats.nba.com/stats/boxscoretraditionalv2?EndPeriod=10&EndRange=28800&GameID=0020901030&RangeType=0&Season=2009-10&SeasonType=Regular+Season&StartPeriod=1&StartRange=0

    PlayByPlay URL:
    http://stats.nba.com/stats/playbyplayv2?GameID=0020901030&SeasonType=Regular+Season&StartPeriod=1&StartRange=0&EndPeriod=10

    TODO:
    Test whether an overtime game (i.e last period > 4) passes the tests
    http://stats.nba.com/game/#!/0021400004/ is a game with overtime

"""
import pytest
from statsnba.models.nba import NBAGame


game_id = '0021400004'


@pytest.fixture(scope='module')
def sample_playbyplays():
    game = NBAGame(game_id='0021400004')
    return game.playbyplay


# Test that the events are correctly parsed
def test_create_playbyplay(sample_playbyplays):
    assert sample_playbyplays[0].game_id == game_id


def test_parse_overtime_playbyplay(sample_playbyplays):
    assert sample_playbyplays[-1].period == 5


def test_game_id(sample_playbyplays):
    assert sample_playbyplays[0].game_id == '0021400004'


def test_shot(sample_playbyplays):
    # test shot made
    assert sample_playbyplays[8].event_type == 'shot made'
    assert sample_playbyplays[8].result == 'made'
    assert sample_playbyplays[8].team == 'MIL'
    # test shot miss
    assert sample_playbyplays[4].event_type == 'shot missed'
    assert sample_playbyplays[4].result == 'missed'
    assert sample_playbyplays[4].team == 'MIL'


def test_free_throw(sample_playbyplays):
    # test free throw made
    assert sample_playbyplays[12].event_type == 'free throw'
    assert sample_playbyplays[12].result == 'made'
    assert sample_playbyplays[12].team == 'MIL'
    assert sample_playbyplays[12].num == '1'
    assert sample_playbyplays[12].outof == '1'
    assert sample_playbyplays[12].player == 'Brandon Knight'
    # test free throw miss
    assert sample_playbyplays[30].event_type == 'free throw'
    assert sample_playbyplays[30].result == 'missed'
    assert sample_playbyplays[30].team == 'CHA'
    assert sample_playbyplays[30].num == '1'
    assert sample_playbyplays[30].outof == '2'
    assert sample_playbyplays[30].player == 'Kemba Walker'


def test_rebound(sample_playbyplays):
    # test offensive rebound
    assert sample_playbyplays[58].event_type == 'offensive rebound'
    assert sample_playbyplays[58].team == 'CHA'
    assert sample_playbyplays[58].player == 'Lance Stephenson'
    # test defensive rebound
    assert sample_playbyplays[72].event_type == 'defensive rebound'
    assert sample_playbyplays[72].team == 'CHA'
    assert sample_playbyplays[72].player == 'Lance Stephenson'


def test_turnover(sample_playbyplays):
    # test turnover
    assert sample_playbyplays[26].event_type == 'turnover'
    assert sample_playbyplays[26].steal == 'Larry Sanders'
    assert sample_playbyplays[26].player == 'Michael Kidd-Gilchrist'
    pytest.xfail()


def test_foul(sample_playbyplays):
    assert sample_playbyplays[63].event_type == 'foul'
    assert sample_playbyplays[63].team == 'CHA'
    assert sample_playbyplays[63].player == 'Michael Kidd-Gilchrist'
    pytest.xfail()


def test_violation(sample_playbyplays):
    assert sample_playbyplays[59].event_type == 'violation'
    assert sample_playbyplays[275].event_type == 'violation'


def test_sub(sample_playbyplays):
    assert sample_playbyplays[32].event_type == 'substitution'
    assert sample_playbyplays[32].team == 'MIL'
    assert sample_playbyplays[32].entered == 'Zaza Pachulia'
    assert sample_playbyplays[32].left == 'Larry Sanders'


def test_timeout(sample_playbyplays):
    assert sample_playbyplays[51].event_type == 'timeout'
    assert sample_playbyplays[92].event_type == 'timeout'
    pytest.xfail('Still need to consider parsing team of timeout')


def test_jumpball(sample_playbyplays):
    assert sample_playbyplays[1].event_type == 'jumpball'
    assert sample_playbyplays[1].team == 'CHA'
    assert sample_playbyplays[1].player == 'Al Jefferson'
    assert sample_playbyplays[1].home == 'Al Jefferson'
    assert sample_playbyplays[1].away == 'Larry Sanders'
    assert sample_playbyplays[1].possession == 'Kemba Walker'


def test_ejection(sample_playbyplays):
    pytest.xfail('no ejection in this sample')


def test_start_period(sample_playbyplays):
    assert sample_playbyplays[0].event_type == 'start of period'
    assert sample_playbyplays[470].event_type == 'start of period'


def test_end_period(sample_playbyplays):
    assert sample_playbyplays[113].event_type == 'end of period'
    assert sample_playbyplays[509].event_type == 'end of period'


# Test that line-ups are correctly aggregated from the playbyplays
def test_lineups():
    pytest.xfail()
