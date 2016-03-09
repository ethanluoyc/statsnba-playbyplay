import re
import functools


def _num_outof(data, group_no):
    descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                    data['NEUTRALDESCRIPTION']]
    for des in descriptions:
        if des:
            m = re.search(r'(\d) of (\d)', des)
            if m:
                return m.group(group_no)

num = functools.partial(_num_outof, group_no=1)
outof = functools.partial(_num_outof, group_no=2)


def result(data):
    if str(data['EVENTMSGTYPE']) == '1': return 'made'
    if str(data['EVENTMSGTYPE']) == '2': return 'missed'
    descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                    data['NEUTRALDESCRIPTION']]
    for des in descriptions:
        if des:
            if re.match(r"^MISS", des):
                return 'missed'
    return 'made'


def _score(data, home_or_away):
    score = data['SCORE']
    if home_or_away == 'home':
        group = 1
    elif home_or_away == 'away':
        group = 2
    else:
        raise Exception('You specified an unknwon flag')
    return group

home_score = functools.partial(_score, home_or_away='home')
away_score = functools.partial(_score, home_or_away='away')


def points(data):
    descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                    data['NEUTRALDESCRIPTION']]
    if str(data['EVENTMSGTYPE']) == '1':
        pts = 2
        for des in descriptions:
            if re.search('3PT', des):
                pts = 3
    elif str(data['EVENTMSGTYPE']) == '2':
        pts = 0
    elif str(data['EVENTMSGTYPE']) == '3':
        pts = 1
    else:
        pts = None
        return pts
    if result(data) == 'missed':
        pts = 0
    return pts


def description(data):
    pass

# The target columns we want to have
column_functions = {'game_id': 'GAME_ID',
                    'period': 'PERIOD',
                    'away_score': away_score,
                    'home_score': home_score,
                    'remaining_time': 'PCTIMESTRING',  # TODO may improve this
                    'elapsed': None,
                    'play_length': None,
                    'play_id': 'EVENTNUM',                                 # TODO disable this
                    'team': 'PLAYER1_TEAM_ABBREVIATION',
                    'event_type': None,  # parsed inside the function
                    'assist': 'PLAYER2_NAME',
                    'away': 'PLAYER2_NAME',
                    'home': 'PLAYER1_NAME',
                    'block': 'PLAYER3_NAME',
                    'entered': 'PLAYER2_NAME',
                    'left': 'PLAYER1_NAME',
                    'num': num,
                    'opponent': 'PLAYER2_NAME',
                    'outof': outof,
                    'player': 'PLAYER1_NAME',
                    'points': points,
                    'possession': 'PLAYER3_NAME',
                    'reason': None,
                    'result': result,
                    'steal': 'PLAYER2_NAME',
                    'type': None,
                    'shot_distance': None,
                    'original_x': None,                              # TODO investigate where to look for this
                    'original_y': None,
                    'converted_x': None,
                    'converted_y': None,
                    'description': description}

all_columns = set(column_functions.keys())
# columns that, depending on the event will have different fill-ins
optional_columns = {'team', 'assist', 'away', 'home', 'block', 'entered', 'left', 'num', 'opponent', 'outof', 'player',
                    'points', 'possession', 'result', 'steal'}

required_columns = all_columns - optional_columns

event_msg_types = [
    (1, 'shot made', ['team', 'assist', 'player', 'result']),
    (2, 'shot miss', ['team', 'block', 'player', 'result']),
    (3, 'free_throw', ['team', 'player', 'num', 'outof', 'result']),
    (4, 'rebound', ['team', 'player']),
    (5, 'turnover', ['team', 'player', 'steal']),
    (6, 'foul', ['team', 'player', 'opponent']),
    (7, 'violation', ['team', 'player']),
    (8, 'substitution', ['team', 'entered', 'left']),
    (9, 'timeout', []),
    (10, 'jumpball', ['team', 'player', 'home', 'away']),
    (11, 'ejection', []),
    (12, 'start_of_period', []),
    (13, 'end_of_period', [])
]

event_table = {}
for event in event_msg_types:
    event_table[str(event[0])] = event[1:]


def parse(data):
    parsed_data = {}
    for k in column_functions.keys():
        parsed_data[k] = None

    def _get_event_type(event_msg_type):
        try:
            et = event_table[event_msg_type]
        except KeyError:
            et = ('unknown', [])
        return et

    def _parse_column(col):
        if hasattr(column_functions[col], '__call__'):
            parsed_data[col] = column_functions[col](data)
        elif column_functions[col]:
            parsed_data[col] = data[column_functions[col]]

    event_type, opt = _get_event_type(str(data['EVENTMSGTYPE']))
    for col in required_columns | set(opt):
        _parse_column(col)
    parsed_data['event_type'] = event_type

    return parsed_data

__all__ = ['parse']
