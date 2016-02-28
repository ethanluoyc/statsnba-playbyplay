event_type = None
num = None
outof = None
result = None
points = None
description = None

# The target columns we want to have
column_functions = {'period': 'PERIOD',
                    'away_score': None,
                    'home_score': None,
                    'remaining_time': None,
                    'elapsed': None,
                    'play_length': None,
                    'play_id': None,  # TODO disable this
                    'team': 'PLAYER1_TEAM_ABBREVIATION',
                    'event_type': event_type,  # parsed inside the function
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
                    'original_x': None,
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
    (1, 'shot made', ['team', 'assist', 'player']),
    (2, 'shot miss', ['team', 'block', 'player']),
    (3, 'free_throw', ['team', 'player', 'num', 'outof']),
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
        return event_table[event_msg_type]

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
