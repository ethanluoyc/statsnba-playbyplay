import re


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


def NBAEvent(event_stats_idx, game=None, on_court_players=None):
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
    event_dict = game._pbp['resultSets']['PlayByPlay'][event_stats_idx]
    event_num = int(event_dict['EVENTMSGTYPE'])
    try:
        return event_mapping[event_num](event_stats_idx, game=game, on_court_players=on_court_players)
    except KeyError:
        return Unknown(event_stats_idx, game=game, on_court_players=on_court_players)


class _NBAEvent(object):
    """
        The class for creating an event instance based on data in the play-by-play
    """
    optional_fields = set()

    def __init__(self, event_stats_idx, game=None, on_court_players=None):
        self._game = game
        self.event_stats_idx = event_stats_idx
        self._players = set()
        self._event_stats = game._pbp['resultSets']['PlayByPlay'][event_stats_idx]
        self._parse_event()
        if on_court_players:
            self._parse_players(on_court_players)

    def __getattr__(self, item):
        try:
            return self._parsed_data[item]
        except KeyError:
            if item in all_fields:  # It needs to be a field parsed
                return None
            import re
            m = re.match('^home_player(\d)_(.*)', item)
            if m:
                players = self.home_players
                return getattr(players[int(m.group(1))-1], m.group(2))
            m = re.match('^away_player(\d)_(.*)', item)
            if m:
                players = self.away_players
                return getattr(players[int(m.group(1))-1], m.group(2))
            raise KeyError(item)

    def __eq__(self, other):
        return self.play_id == other.play_id and \
               self.game_id == other.game_id

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' ' + str(self.event_stats_idx) + ' >'

    def _parse_players(self, on_court_players):
        _on_court_copy = on_court_players.copy()
        # forward looking for the current 10 players on the floor by relying the API
        if self.period > NBAEvent(self.event_stats_idx - 1, game=self._game).period:
            start_range = self.overall_elapsed_time.seconds * 10 + 5
            to_update_floor_players = True
            j = self.event_stats_idx
            while to_update_floor_players:
                forward_ev = NBAEvent(j, game=self._game)
                if forward_ev.event_type == 'substitution':
                    end_range = forward_ev.overall_elapsed_time.seconds * 10
                    on_court_players = self._game.find_players_in_range(start_range, end_range)
                    while len(on_court_players) != 10:
                        end_range -= 5
                        if end_range <= start_range:
                            raise AssertionError(
                                'could not locate on floor players %s, %s' % (start_range, end_range))
                        on_court_players = self._game.find_players_in_range(start_range, end_range)
                    to_update_floor_players = False
                else:
                    j += 1
                    if j == len(self._game._pbp['resultSets']['PlayByPlay'][j]):
                        end_range = forward_ev.overall_elapsed_time.seconds * 10
                        on_court_players = self.find_players_in_range(start_range, end_range)
                        to_update_floor_players = False
        if self.event_type == 'substitution':
            on_court_players.remove(self._game._find_player(self.left))
            on_court_players.add(self._game._find_player(self.entered))
            assert on_court_players != _on_court_copy
        self.update_players(on_court_players)
        self.on_court_players = on_court_players

    def _parse_event(self):
        self._parsed_data = {}

        self.fields = self.optional_fields | required_fields

        for col in column_functions:
            field = col[1]
            parse_func = col[2]
            if field in self.fields:
                if parse_func:
                    self._parsed_data[field] = self._event_stats[parse_func]

    def to_dict(self, fields=None):
        if not fields:
            fields = []
        d = self._parsed_data.copy()
        home_cols = ['h1', 'h2', 'h3', 'h4', 'h5']
        away_cols = ['a1', 'a2', 'a3', 'a4', 'a5']
        hps = dict(zip(home_cols, self.home_players))
        aps = dict(zip(away_cols, self.away_players))
        d.update({
            'period_elapsed_time': self.period_elapsed_time,
            'overall_elapsed_time': self.overall_elapsed_time
        })
        d.update(hps)
        d.update(aps)
        if fields:
            return {k: v for k, v in d.items() if k in fields}
        return d

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
            if p.team_abbr == self._game.home_team:
                players.append(p)
        return sorted(players)

    @property
    def away_players(self):
        players = []
        for p in self._players:
            if p.team_abbr == self._game.away_team:
                players.append(p)
        return sorted(players)

    def update_players(self, players):
        self._players = self._players | players

    @property
    def period_length(self):
        from datetime import timedelta
        period_time_total = timedelta(minutes=5) if int(self.period) > 4 else timedelta(minutes=12)

        return period_time_total

    @staticmethod
    def _parse_pctimestring(timestring):
        from datetime import datetime, timedelta
        time = datetime.strptime(timestring, '%M:%S')  # parse minutes like this '10:29'
        return timedelta(minutes=time.minute, seconds=time.second)

    @property
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
        return score[group - 1].strip()

    @property
    def home_score(self):
        return self._score(self._event_stats, 'home')

    @property
    def away_score(self):
        return self._score(self._event_stats, 'away')

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
    optional_fields = {'team', 'assist', 'player', 'result'}

    @property
    def event_type(self):
        if str(self._event_stats['EVENTMSGTYPE']) == '1':
            return 'shot made'
        if str(self._event_stats['EVENTMSGTYPE']) == '2':
            return 'shot missed'


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
        try:
            assert prev_event.event_type in ['shot missed', 'free throw', 'jumpball']
        except AssertionError:
            raise AssertionError('Previous event is %s, %s' % (prev_event, prev_event.event_type))
        if prev_event.team == self.team:
            event_type = 'offensive rebound'
        else:
            event_type = 'defensive rebound'
        return event_type


class Foul(_NBAEvent):
    event_type = 'foul'
    optional_fields = {'team', 'player', 'steal'}


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
