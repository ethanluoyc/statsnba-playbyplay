from .parse import parse


class StatsNBAProxy(object):
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, item):
        return self._obj[item]


class Team(object):
    def __init__(self, team_stats):
        self._stats = team_stats


class Player(StatsNBAProxy):
    STARTER_POSITION = 'starters'
    BENCH_POSITION = 'bench'

    def __init__(self, player_stats):
        super(Player, self).__init__(player_stats)
        self._stats = player_stats
        self.name = player_stats['PLAYER_NAME']
        self.team_abbr = player_stats['TEAM_ABBREVIATION']
        self.start_position = self.starter_or_bench(player_stats)

    @staticmethod
    def starter_or_bench(player_stats):
        if player_stats['START_POSITION']:
            return 'starters'
        else:
            return 'bench'

    def __eq__(self, other):
        return self.name == other.name and self.team_abbr == self.team_abbr

    def __repr__(self):
        return '<{}>'.format(self.name)

    def __str__(self):
        return self.name

class Event(StatsNBAProxy):

    def __init__(self, event_data):
        self._obj = parse(event_data)

    def __repr__(self):
        return self.event_type

    def __str__(self):
        return self.event_type


class Game(object):
    def __init__(self, boxscore_data, playbyplay_data, mapper=None):  #todo args seem cumbersome, can delegate
        self._boxscore = boxscore_data
        self._pbp = playbyplay_data
        self._players = []
        self._mapper = mapper

        for player in self._boxscore['resultSets']['PlayerStats']:
            self._players.append(Player(player))

    @property
    def home_team(self):
        return self._boxscore['resultSets']['TeamStats'][0]['TEAM_ABBREVIATION']

    @property
    def away_team(self):
        return self._boxscore['resultSets']['TeamStats'][1]['TEAM_ABBREVIATION']

    def _select_players(self, team, starter_or_bench):
        selected = []
        for p in self._players:
            if p.team_abbr == getattr(self, team) and p.start_position == starter_or_bench:
                selected.append(p)
        return selected

    @property
    def home_starters(self):
        return self._select_players('home_team', 'starters')

    @property
    def home_bench(self):
        return self._select_players('home_team', 'bench')

    @property
    def away_starters(self):
        return self._select_players('away_team', 'starters')

    @property
    def away_bench(self):
        return self._select_players('away_team', 'bench')

    @property
    def playbyplay(self):
        on_court_players = self.home_starters + self.away_starters
        pbp = []

        for i, p in enumerate(self._pbp['resultSets']['PlayByPlay']):
            ev = Event(p)
            if ev.event_type == 'substitution':
                for j, player in enumerate(on_court_players):
                    if player.name == ev.left:
                        on_court_players[j].name = ev.entered
            elif ev.period > Event(self._pbp['resultSets']['PlayByPlay'][i-1]).period:
                pass
            pbp.append([on_court_players[:], ev])
        return pbp


