import pytest
from statsnba import Api, Game


def pytest_addoption(parser):
    parser.addoption("--use-cache", action="store_true",
                     help="True to use requests_cache")


def pytest_configure(config):
    if config.getoption('--use-cache'):
        import requests_cache
        requests_cache.install_cache('test_cache')
    api = Api()
    pytest.game_ids = api.GetSeasonGameIDs('2009-10', 'Regular Season')[:2]  # Hack to carry the gameids to tests
    pytest.game_ids = ['0020900292']


def pytest_generate_tests(metafunc):
    game_ids = pytest.game_ids
    if 'game' in metafunc.fixturenames:
        metafunc.parametrize('game', game_ids, indirect=True, ids=idfn)


def idfn(game_id):
    return 'GameId=' + game_id


@pytest.fixture
def game(request):
    print 'Starting to test for game %s' % request.param
    return Game(request.param)
