import pytest
from models.nba import NBAGame

game_id = '0020901030'


@pytest.fixture(scope='module')
def sample_game():
    game = NBAGame(game_id)
    return game


def test_create_playbyplay(sample_game):
    pbps = sample_game.playbyplay
    assert pbps[0].game_id == game_id


# a game with overtime (i.e. period 5) "0021400004"
def test_parse_overtime_playbyplay():
    pass
