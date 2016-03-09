import re
import functools


def create_event(event_dict, game=None):
    pass


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

# (is_it_required, event_attr, event_data_key)
column_functions = ((True, 'game_id', 'GAME_ID'),
                    (True, 'period', 'PERIOD'),
                    (True, 'away_score', away_score),
                    (True, 'home_score', home_score),
                    (True, 'remaining_time', 'PCTIMESTRING'),
                    (True, 'elapsed', None),
                    (True, 'play_length', None),
                    (True, 'play_id', 'EVENTNUM'),
                    (False, 'team', 'PLAYER1_TEAM_ABBREVIATION'),
                    (True, 'event_type', None),
                    (False, 'assist', 'PLAYER2_NAME'),
                    (False, 'away', 'PLAYER2_NAME'),
                    (False, 'home', 'PLAYER1_NAME'),
                    (False, 'block', 'PLAYER3_NAME'),
                    (False, 'entered', 'PLAYER2_NAME'),
                    (False, 'left', 'PLAYER1_NAME'),
                    (False, 'num', num),
                    (False, 'opponent', 'PLAYER2_NAME'),
                    (False, 'outof', outof),
                    (False, 'player', 'PLAYER1_NAME'),
                    (False, 'points', points),
                    (False, 'possession', 'PLAYER3_NAME'),
                    (True, 'reason', None),
                    (False, 'result', result),
                    (False, 'steal', 'PLAYER2_NAME'),
                    (True, 'type', None),
                    (False, 'shot_distance', None),
                    (True, 'original_x', None),
                    (True, 'original_y', None),
                    (True, 'converted_x', None),
                    (True, 'converted_y', None),
                    (False, 'description', description))

all_fields = {c[1] for c in column_functions}
required_fields = {c[1] for c in column_functions if c[0]}

event_msg_types = (
    (1, 'shot made', {'team', 'assist', 'player', 'result'}),
    (2, 'shot miss', {'team', 'block', 'player', 'result'}),
    (3, 'free_throw', {'team', 'player', 'num', 'outof', 'result'}),
    (4, 'rebound', {'team', 'player'}),
    (5, 'turnover', {'team', 'player', 'steal'}),
    (6, 'foul', {'team', 'player', 'opponent'}),
    (7, 'violation', {'team', 'player'}),
    (8, 'substitution', {'team', 'entered', 'left'}),
    (9, 'timeout', {}),
    (10, 'jumpball', {'team', 'player', 'home', 'away'}),
    (11, 'ejection', {}),
    (12, 'start_of_period', {}),
    (13, 'end_of_period', {})
)

event_msg_mapping = {str(ev[0]): (ev[1], ev[2]) for ev in event_msg_types}


class NBAEvent(object):

    def __init__(self, event_stats):
        self._event_stats = event_stats
        self._parsed_data = {}
        for k in all_fields:
            self._parsed_data[k] = None
        try:
            event_type, optional_fields = event_msg_mapping[str(event_stats['EVENTMSGTYPE'])]
        except KeyError:
            event_type = 'unknown'
            optional_fields = {}

        for col in column_functions:
            field = col[1]
            parse_func = col[2]
            if field in optional_fields | required_fields:
                if hasattr(parse_func, '__call__'):
                    self._parsed_data[col] = event_stats[parse_func(event_stats)]
                else:
                    self._parsed_data[col] = event_stats[parse_func]

        self._parsed_data['event_type'] = event_type

    def __getattr__(self, item):
        return self._parsed_data[item]

    @classmethod
    def parse(cls, data):
        parsed_data = {}
        for k in all_fields:
            parsed_data[k] = None
        try:
            event_type, optional_fields = event_msg_mapping[str(data['EVENTMSGTYPE'])]
        except KeyError:
            event_type = 'unknown'
            optional_fields = {}

        for col in column_functions:
            field = col[1]
            parse_func = col[2]
            if field in optional_fields | required_fields:
                if hasattr(parse_func, '__call__'):
                    parsed_data[col] = data[parse_func(data)]
                else:
                    parsed_data[col] = data[parse_func]

        parsed_data['event_type'] = event_type

        return parsed_data


class Shot(NBAEvent):
    required_fields = {'team', 'assist', 'player', 'result'}


class FreeThrow(NBAEvent):
    required_fields = {'team', 'player', 'num', 'outof', 'result'}


class Rebound(NBAEvent):
    required_fields = {'team', 'player'}


class Foul(NBAEvent):
    required_fields = {'team', 'player', 'steal'}


class Violation(NBAEvent):
    required_fields = {'team', 'player'}


class Substitution(NBAEvent):
    required_fields = {'team', 'entered', 'left'}


class Timeout(NBAEvent):
    required_fields = {}


class Turnover(NBAEvent):
    required_fields = {'team', 'player', 'steal'}


class Jumpball(NBAEvent):
    required_fields = {'team', 'player', 'home', 'away'}


class Ejection(NBAEvent):
    required_fields = {}


class StartPeriod(NBAEvent):
    required_fields = {}


class EndPeriod(NBAEvent):
    required_columns = {}


class Unknown(NBAEvent):
    required_columns = {}
    pass

__all__ = ['create_event']
