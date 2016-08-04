import pytest
from os import path
from statsnba.models import Game, Model

SAMPLEDATA_DIR = path.join(path.dirname(__file__), '../sample_data/')


def pytest_runtest_setup(item):
        # called for running each test in 'a' directory
    import requests_cache
    requests_cache.install_cache('test_cache')


def pytest_collect_file(parent, path):
    if path.ext == ".yml" and path.basename.startswith("event"):
        return EventFile(path, parent)


class EventFile(pytest.File):
    def collect(self):
        import yaml
        raw = yaml.safe_load(self.fspath.open())
        tests = []
        game_id = self.fspath.purebasename.split('_')[-1]
        game = Game(game_id)
        for cat, events in raw.items():
            if events:
                tests.append(EventTypeCollector(self, events, cat, game.PlayByPlay))
        return tests


class EventTypeCollector(pytest.Collector):
    """Collect all the specs in a particular EventType"""
    def __init__(self, parent, events, name, pbp):
        super(EventTypeCollector, self).__init__(name, parent=parent)
        self.events = events
        self.pbp = pbp

    def collect(self):
        tests = []
        for event in self.events:
            tests.append(Event(event['index'], self, event))
        return tests


class Event(pytest.Item):
    def __init__(self, index, parent, event):
        self.index= index
        self.event = event
        self._pbp = parent.pbp
        name = '%s, eventnum: %s' % (parent.name, self.index)
        super(Event, self).__init__(name, parent)

    @staticmethod
    def assert_model(actual, expected_dict):
        for k, v in expected_dict.items():
            assert getattr(actual, k) == v

    def _assert_event(self):
        actual = self._pbp[self.index]
        self.event.pop('index')
        for key, value in self.event.items():
            event_attr = getattr(actual, key)
            try:
                if isinstance(event_attr, Model):
                    Event.assert_model(event_attr, value)
                else:
                    assert event_attr == value
            except AssertionError as e:
                raise FieldMismatchError(str(e))

    def runtest(self):
        self._assert_event()

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, FieldMismatchError):
            return str(excinfo.value)

    def reportinfo(self):
        return self.fspath, None, self.name


class FieldMismatchError(Exception):
    pass
