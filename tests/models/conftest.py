import pytest
import sys
from os import path
from statsnba.models import Game


SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test



def pytest_collect_file(parent, path):
    if path.ext == ".yml" and path.basename.startswith("test"):
        return YamlFile(path, parent)


@pytest.fixture(scope='session')
def sample_boxscore():
    import json
    with open(path.join(SAMPLEDATA_DIR, 'sample_boxscore.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def sample_playbyplay():
    import json
    with open(path.join(SAMPLEDATA_DIR, 'sample_playbyplay.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def sample_game_id():
    return '0020901030'


@pytest.fixture(scope='session')
def game(sample_game_id, sample_playbyplay, sample_boxscore):
    return Game(sample_game_id, sample_boxscore, sample_playbyplay)


class YamlFile(pytest.File):
    def collect(self):
        # Our spec is tree like, so we have to run recursively till bottom
        import yaml
        import json

        with open(path.join(SAMPLEDATA_DIR, 'sample_playbyplay.json'), 'r') as f:
            playbyplay = json.load(f)
        with open(path.join(SAMPLEDATA_DIR, 'sample_boxscore.json')) as f:
            boxscore = json.load(f)

        raw = yaml.safe_load(self.fspath.open())
        tests = []
        for name, spec in raw.items():
            game = Game('0020901030', boxscore=boxscore, playbyplays=playbyplay)
            tests.append(YamlCollector(self, spec, name, game))
        return tests


class YamlCollector(pytest.Collector):
    def __init__(self, parent, target, name, ctx):
        super(YamlCollector, self).__init__(name, parent=parent)
        self.ctx = ctx
        self.target = target

    def _get_ctx_val(self, key):
        # Some fields are recorded as dicts, so use this to retrieve value
        if isinstance(self.ctx, dict):
            return self.ctx[key]
        else:
            return getattr(self.ctx, key)

    def collect(self):
        tests = []
        for name, value in self.target.items():
            if not isinstance(value, dict):
                tests.append(YamlItem(name, self, value, self._get_ctx_val(name)))
            else:
                tests = tests + YamlCollector(self, value, name,
                                              getattr(self.ctx, name)).collect()
        return tests


class YamlItem(pytest.Item):
    # The atomic test
    def __init__(self, name, parent, expected, actual):
        super(YamlItem, self).__init__(name, parent)
        self.expected = expected
        self.actual = actual

    def runtest(self):
        assert self.expected == self.actual


@pytest.fixture(autouse=True)
def use_pytest_tmp_dir(monkeypatch, tmpdir_factory):
    tmp_dir = tmpdir_factory.getbasetemp()
    monkeypatch.setattr('tempfile.mkdtemp', lambda: str(tmp_dir))
    return tmp_dir


@pytest.fixture(scope='session', autouse=True)
def use_requests_cache():
    import requests_cache
    requests_cache.install_cache('test_cache')

