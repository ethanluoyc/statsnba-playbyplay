from os import path
import pytest
from statsnba.parse import parse

SAMPLEDATA_DIR = path.join(path.dirname(__file__), 'sample_data/')


@pytest.fixture()
def event():
    pass


def test_parse():
    import pandas as pd
    records = pd.read_csv(path.join(SAMPLEDATA_DIR, 'events.csv')).to_dict(orient='records')
    assert records[0]['EVENTMSGTYPE'] == 1
    event = parse(records[0])
    assert event['event_type'] == 'shot made'
    assert event['converted_y'] is None
    assert event['player'] == 'Ty Lawson'
