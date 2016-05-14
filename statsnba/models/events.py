import re
import logging
from cached_property import cached_property

logger = logging.getLogger(__name__)

#         (is_it_required, event_attr, event_data_key)
column_functions = ((True, 'game_id', 'GAME_ID'),
                    (True, 'period', 'PERIOD'),
                    (True, 'away_score', None),
                    (True, 'home_score', None),
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
                    (False, 'num', None),
                    (False, 'opponent', 'PLAYER2_NAME'),
                    (False, 'outof', None),
                    (False, 'player', 'PLAYER1_NAME'),
                    (False, 'points', None),
                    (False, 'possession', 'PLAYER3_NAME'),
                    (True, 'reason', None),
                    (False, 'result', None),
                    (False, 'steal', 'PLAYER2_NAME'),
                    (True, 'type', None),
                    (False, 'shot_distance', None),  # TODO complete shot log
                    (True, 'original_x', None),
                    (True, 'original_y', None),
                    (True, 'converted_x', None),
                    (True, 'converted_y', None),
                    (False, 'description', None))

all_fields = {c[1] for c in column_functions}
required_fields = {c[1] for c in column_functions if c[0]}


def NBAEvent(event_stats_idx, game=None):
    event_mapping = {
        1: Shot,
        2: Shot,
        3: FreeThrow,
        4: Rebound,
        5: Turnover,
        6: Foul,
        7: Violation,
        8: Substitution,
        9: Timeout,
        10: Jumpball,
        11: Ejection,
        12: StartOfPeriod,
        13: EndOfPeriod
    }
    event_dict = game._get_playbyplay()[event_stats_idx]
    event_num = int(event_dict['EVENTMSGTYPE'])
    try:
        return event_mapping[event_num](event_stats_idx, game=game)
    except KeyError:
        return Unknown(event_stats_idx, game=game)


class _NBAEvent(object):
    """
        The class for creating an event instance based on data in the play-by-play
    """
    optional_fields = set()

    def __init__(self, event_stats_idx, game=None):
        self._game = game
        self.event_stats_idx = event_stats_idx
        self._players = set()
        self._event_stats = game._get_playbyplay()[event_stats_idx]
        self._parse_event()

    def __getattr__(self, item):
        try:
            return self._parsed_data[item]
        except KeyError:
            raise AttributeError

    def __eq__(self, other):
        return self.play_id == other.play_id and \
               self.game_id == other.game_id

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' ' + str(self.play_id) + ' >'

    def _parse_event(self):
        self._parsed_data = {}

        self.fields = self.optional_fields | required_fields

        for col in column_functions:
            field = col[1]
            parse_func = col[2]
            if field in self.fields:
                if parse_func:
                    self._parsed_data[field] = self._event_stats[parse_func]

    def to_dict(self):
        fields = (
            'game_id,period,away_score,home_score,home_team,away_team,'
            'play_id,team,event_type,away,home,block,assist,'
            'entered,left,num,opponent,outof,player,points,possession,'
            'reason,result,steal,type,'
            'shot_distance,original_x,original_y,converted_x,converted_y,'
            'description,period_elapsed_time,period_remaining_time,'
            'overall_elapsed_time,overall_remaining_time'
        ).split(',')
        return {f: getattr(self, f, None) for f in fields}

    @staticmethod
    def update_game_players(events):
        """Update the players in each row of the playbyplays"""
        game = events[0]._game
        for i, ev in enumerate(events):
            if i == 0:
                ev.update_players(game.home_starters | game.away_starters)
                continue
            prev_ev = events[i-1]
            on_court_players = prev_ev.players.copy()
            _on_court_copy = on_court_players.copy()
            # If another period, then it should fetch players starting the period from the API
            if ev.period > prev_ev.period:
                start_range = ev.overall_elapsed_time.seconds * 10 + 5
                j = i
                to_update_floor_players = True
                while to_update_floor_players:   # Locate the range to look up for the players
                    forward_ev = events[j]
                    if forward_ev.event_type == 'substitution':
                        end_range = forward_ev.overall_elapsed_time.seconds * 10
                        on_court_players = game.find_players_in_range(start_range, end_range)
                        while len(on_court_players) != 10:
                            end_range -= 5
                            if end_range <= start_range:
                                raise AssertionError(
                                    'Could not locate on floor players %s, %s' % (start_range, end_range))
                            on_court_players = game.find_players_in_range(start_range, end_range)
                        to_update_floor_players = False
                    else:
                        j += 1
                        if j == len(game._playbyplay['resultSets']['PlayByPlay']):
                            # if no sub at all after the increase in period, \
                            # then find the players on court of all remaining time.
                            end_range = forward_ev.overall_elapsed_time.seconds * 10
                            on_court_players = game.find_players_in_range(start_range, end_range)
                            assert len(on_court_players) == 10
                            to_update_floor_players = False
            if ev.event_type == 'substitution':
                on_court_players.remove(game._find_player(ev.left))
                on_court_players.add(game._find_player(ev.entered))
                assert on_court_players != _on_court_copy
            ev.update_players(on_court_players)
        return events

# Below are the parsed properties.

    @property
    def home_team(self):
        return self._game.home_team

    @property
    def away_team(self):
        return self._game.away_team

    @property
    def players(self):
        if self._players:
            return self._players
        else:
            raise Exception('You have not updated the players')

    @property
    def home_players(self):
        players = []
        for p in self._players:
            if p.team == self._game.home_team:
                players.append(p)
        return set(players)

    @property
    def away_players(self):
        players = []
        for p in self._players:
            if p.team == self._game.away_team:
                players.append(p)
        return set(players)

    def update_players(self, players):
        self._players = self._players | players

    @cached_property
    def period_length(self):
        from datetime import timedelta
        period_time_total = timedelta(minutes=5) if int(self.period) > 4 else timedelta(minutes=12)

        return period_time_total

    @staticmethod
    def _parse_pctimestring(timestring):
        from datetime import datetime, timedelta
        time = datetime.strptime(timestring, '%M:%S')  # parse minutes like this '10:29'
        return timedelta(minutes=time.minute, seconds=time.second)

    @cached_property
    def period_elapsed_time(self):
        return self.period_length - self._parse_pctimestring(self.remaining_time)

    @property
    def period_remaining_time(self):
        return self._parse_pctimestring(self.remaining_time)

    @property
    def overall_length(self):
        return self._game.game_length

    @property
    def overall_elapsed_time(self):
        from datetime import timedelta
        if self.period > 4:
            return timedelta(minutes=(int(self.period) - 5) * 5 + 12 * 4) + self.period_elapsed_time
        else:
            return timedelta(minutes=(int(self.period) - 1) * 12) + self.period_elapsed_time

    @property
    def overall_remaining_time(self):
        return self.overall_length - self.overall_elapsed_time

    @staticmethod
    def _score(data, home_or_away):
        if not data['SCORE']:
            return None
        score = data['SCORE'].split('-')
        if home_or_away == 'home':
            group = 1
        elif home_or_away == 'away':
            group = 2
        else:
            raise Exception('You specified an unknwon flag')
        return int(score[group - 1].strip())

    # TODO refactor this
    @cached_property
    def home_score(self):
        score =  self._score(self._event_stats, 'home')
        stats_idx = self.event_stats_idx
        while not score:
            if stats_idx == 0:
                return 0
            else:
                stats_idx -= 1
                stats = self._game._get_playbyplay()[stats_idx]
                score = self._score(stats, 'home')
        return score

    @cached_property
    def away_score(self):
        # return self._score(self._event_stats, 'away')
        score =  self._score(self._event_stats, 'away')
        stats_idx = self.event_stats_idx
        while not score:
            if stats_idx == 0:
                return 0
            else:
                stats_idx -= 1
                stats = self._game._get_playbyplay()[stats_idx]
                score = self._score(stats, 'away')
        return score


    @property
    def points(self):
        data = self._event_stats
        descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                        data['NEUTRALDESCRIPTION']]
        if str(data['EVENTMSGTYPE']) == '1':
            pts = 2
            for des in descriptions:
                if des is None:
                    des = ''
                if re.search('3PT', des):
                    pts = 3
        elif str(data['EVENTMSGTYPE']) == '2':
            pts = 0
        elif str(data['EVENTMSGTYPE']) == '3':
            pts = 1
        else:
            pts = None
            return pts
        if self.result == 'missed':
            pts = 0
        return pts

    @property
    def description(self):
        return None

    @staticmethod
    def _num_outof(data, group_no):
        descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                        data['NEUTRALDESCRIPTION']]
        for des in descriptions:
            if des:
                m = re.search(r'(\d) of (\d)', des)
                if m:
                    return m.group(group_no)

    @property
    def num(self):
        return self._num_outof(self._event_stats, 1)

    @property
    def outof(self):
        return self._num_outof(self._event_stats, 2)

    @property
    def result(self):
        data = self._event_stats
        if str(data['EVENTMSGTYPE']) == '1': return 'made'
        if str(data['EVENTMSGTYPE']) == '2': return 'missed'
        descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                        data['NEUTRALDESCRIPTION']]
        for des in descriptions:
            if des:
                if re.match(r"^MISS", des):
                    return 'missed'
        return 'made'


class Shot(_NBAEvent):
    optional_fields = {'team', 'assist', 'player', 'result', 'block'}

    @property
    def event_type(self):
        if str(self._event_stats['EVENTMSGTYPE']) == '1':
            return 'shot made'
        if str(self._event_stats['EVENTMSGTYPE']) == '2':
            return 'shot missed'

    @property
    def type(self):
        data = self._event_stats
        descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                        data['NEUTRALDESCRIPTION']]
        for des in descriptions:
            if des is None:
                    des = ''
            if re.search('3PT', des):
                return '3 points'


class FreeThrow(_NBAEvent):
    event_type = 'free throw'
    optional_fields = {'team', 'player', 'num', 'outof', 'result'}

    @property
    def result(self):
        descriptions = [self._event_stats['HOMEDESCRIPTION'], self._event_stats['VISITORDESCRIPTION'],
                    self._event_stats['NEUTRALDESCRIPTION']]
        for des in descriptions:
            if des:
                if re.match(r"^MISS", des):
                    return 'missed'
        return 'made'


class Rebound(_NBAEvent):
    optional_fields = {'team', 'player'}

    @property
    def event_type(self):
        prev_event = NBAEvent(self.event_stats_idx - 1, game=self._game)
        while prev_event.event_type not in ['shot missed', 'free throw', 'jumpball']:
            event_stats_idx = prev_event.event_stats_idx - 1
            assert event_stats_idx > 0
            prev_event = NBAEvent(event_stats_idx, game=self._game)
        if prev_event.team == self.team:
            event_type = 'offensive rebound'
        else:
            event_type = 'defensive rebound'
        return event_type


class Foul(_NBAEvent):
    event_type = 'foul'
    optional_fields = {'team', 'player'}


class Violation(_NBAEvent):
    event_type = 'violation'
    optional_fields = {'team', 'player'}


class Substitution(_NBAEvent):
    event_type = 'substitution'
    optional_fields = {'team', 'entered', 'left'}


class Timeout(_NBAEvent):
    event_type = 'timeout'


class Turnover(_NBAEvent):
    event_type = 'turnover'
    optional_fields = {'team', 'player', 'steal'}


class Jumpball(_NBAEvent):
    event_type = 'jumpball'
    optional_fields = {'team', 'player', 'home', 'away', 'possession'}


class Ejection(_NBAEvent):
    event_type = 'ejection'


class StartOfPeriod(_NBAEvent):
    event_type = 'start of period'


class EndOfPeriod(_NBAEvent):
    event_type = 'end of period'


class Unknown(_NBAEvent):
    event_type = 'unknown'


__all__ = ['NBAEvent']
