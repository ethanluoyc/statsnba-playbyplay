from ..loaders import FsLoader
from ..resources import StatsNBABoxscore
from statsnba.parse import parse


class NBATeam(object):
    def __init__(self):
        pass

    def __eq__(self, other_team):
        pass


class NBAPlayer(object):
    STARTER_POSITION = 'starters'
    BENCH_POSITION = 'bench'

    def __init__(self, player_stats):
        self.name = player_stats['PLAYER_NAME']
        self.team_abbr = player_stats['TEAM_ABBREVIATION']
        self.start_position = player_stats['START_POSITION']
        self._player_stats = player_stats

    def __getattr__(self, item):
        return self._player_stats[item]

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return self.name == other.name and self.team_abbr == other.team_abbr

    def __repr__(self):
        return '<{}, {}>'.format(self.name, self.team_abbr)

    def __str__(self):
        return self.name

    @property
    def starter_or_bench(self):
        if self.start_position:
            return 'starters'
        return 'bench'


class NBAEvent(object):
    def __init__(self, event_data, game=None):
        self._data = parse(event_data)
        self._game = game
        self._players = set()

    def __getattr__(self, item):
        try:
            return getattr(self._data, item)
        except AttributeError:
            return self._data[item]

    def __eq__(self, other):
        return self._data['play_id'] == other._data['play_id'] and \
                self._data['game_id'] == other._data['game_id']

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
        return players

    @property
    def away_players(self):
        players = []
        for p in self._players:
            if p.team_abbr == self._game.away_team:
                players.append(p)
        return players

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
    def overall_elapsed_time(self):
        from datetime import timedelta
        if self.period > 4:
            return timedelta(minutes=(int(self.period) - 5) * 5 + 12 * 4) + self.period_elapsed_time
        else:
            return timedelta(minutes=(int(self.period) - 1) * 12) + self.period_elapsed_time

    def to_dict(self):
        d = self._data.copy()
        hps = dict(zip(['h1', 'h2', 'h3', 'h4', 'h5'], self.home_players))
        aps = dict(zip(['a1', 'a2', 'a3', 'a4', 'a5'], self.away_players))
        d.update({
            'period_elapsed_time': self.period_elapsed_time,
            'overall_elapsed_time': self.overall_elapsed_time
        })
        d.update(hps)
        d.update(aps)
        return d


class NBAGame(object):
    def __init__(self, game_id, loader=None):
        if loader:
            self._loader = loader
        else:
            from statsnba.loaders import MongoLoader
            self._loader = MongoLoader()
        self.game_id = game_id
        self._boxscore = self._loader.get_boxscore(game_id)
        self._pbp = self._loader.get_playbyplay(game_id)
        self._players = set(map(lambda p: NBAPlayer(player_stats=p), self._boxscore['resultSets']['PlayerStats']))
        self._playbyplay = []

    @property
    def home_team(self):
        return self._boxscore['resultSets']['TeamStats'][0]['TEAM_ABBREVIATION']

    @property
    def away_team(self):
        return self._boxscore['resultSets']['TeamStats'][1]['TEAM_ABBREVIATION']

    def _select_players(self, team, starter_or_bench):
        selected = []
        for p in self._players:
            if p.team_abbr == getattr(self, team) and p.starter_or_bench == starter_or_bench:
                selected.append(p)
        return set(selected)

    @property
    def home_starters(self):
        return self._select_players(team='home_team', starter_or_bench='starters')

    @property
    def home_bench(self):
        return self._select_players(team='home_team', starter_or_bench='bench')

    @property
    def away_starters(self):
        return self._select_players(team='away_team', starter_or_bench='starters')

    @property
    def away_bench(self):
        return self._select_players(team='away_team', starter_or_bench='bench')

    @property
    def playbyplay(self):
        if self._playbyplay:
            return self._playbyplay
        """Playbyplay is the collection of events"""
        on_court_players = self.home_starters | self.away_starters
        pbp = []
        start_range = 0
        to_update_floor_players = False
        for i, p in enumerate(self._pbp['resultSets']['PlayByPlay']):
            ev = NBAEvent(p, game=self)
            _on_court_copy = on_court_players.copy()
            # forward looking for the current 10 players on the floor by relying the API
            if ev.period > NBAEvent(self._pbp['resultSets']['PlayByPlay'][i-1]).period:
                start_range = ev.overall_elapsed_time.seconds * 10 + 10
                to_update_floor_players = True
                j = i
                while to_update_floor_players:
                    forward_ev = NBAEvent(self._pbp['resultSets']['PlayByPlay'][j], game=self)
                    if forward_ev.event_type == 'substitution':
                        end_range = forward_ev.overall_elapsed_time.seconds * 10
                        on_court_players = self.find_players_in_range(start_range, end_range)
                        assert(len(on_court_players)) == 10
                        to_update_floor_players = False
                    else:
                        j += 1
            if ev.event_type == 'substitution':
                on_court_players.remove(self._find_player(ev.left))
                on_court_players.add(self._find_player(ev.entered))
                assert on_court_players != _on_court_copy
            ev.update_players(on_court_players)
            pbp.append(ev)
        self._playbyplay = pbp
        return self._playbyplay

    def find_players_in_range(self, start_range, end_range):
        box = StatsNBABoxscore()
        range_boxscore = box.find_boxscore_in_range(self.game_id, start_range, end_range)
        return set(map(NBAPlayer, range_boxscore['resultSets']['PlayerStats']))

    def _find_player(self, player_name):
        """use player's name and team to find the player"""
        for p in self._players:
            if p.name == player_name:
                return p
        raise Exception('%s is not found in this game' % player_name)
