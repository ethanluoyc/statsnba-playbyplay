from statsnba.mongo import Game


def test_create_game(mongodb):
    game = Game.create_game('0020901030')
    assert game.game_id == '0020901030'
