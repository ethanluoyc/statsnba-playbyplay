import pytest
import sys


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test


def pytest_generate_tests(metafunc):
    pass


@pytest.fixture(autouse=True)
def use_pytest_tmp_dir(monkeypatch, tmpdir_factory):
    tmp_dir = tmpdir_factory.getbasetemp()
    monkeypatch.setattr('tempfile.mkdtemp', lambda: str(tmp_dir))
    return tmp_dir


@pytest.fixture(scope='session', autouse=True)
def use_requests_cache():
    import requests_cache
    requests_cache.install_cache('test_cache')


@pytest.fixture(scope='function')
def mongodb():
    from mongoengine import connect
    from mongoengine.connection import get_connection

    connect('statsnba_test', host='mongomock://localhost')
    conn = get_connection()
    return conn
