from statsnba.resources import StatsNBABoxscore
from events import NBAEvent


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
        return '<Player {}, {}>'.format(self.name, self.team_abbr)

    def __str__(self):
        return self.name

    @property
    def starter_or_bench(self):
        if self.start_position:
            return 'starters'
        return 'bench'


class NBAGame(object):
    def __init__(self, game_id, loader=None):
        if loader:
            self._loader = loader
        else:
            from statsnba.loaders import WebLoader
            self._loader = WebLoader()
        self.game_id = game_id
        self._boxscore = self._loader.get_boxscore(game_id)
        self._pbp = self._loader.get_playbyplay(game_id)
        self._players = set(map(lambda p: NBAPlayer(player_stats=p), self._boxscore['resultSets']['PlayerStats']))
        self._playbyplay = []

    def __repr__(self):
        return self.__class__.__name__ + ' ' + self.game_id

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
        for i, p in enumerate(self._pbp['resultSets']['PlayByPlay']):
            ev = NBAEvent(i, game=self, on_court_players=on_court_players)
            on_court_players = ev.on_court_players
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


class NBALineups(object):
    def __init__(self, playbyplays):
        self._playbyplays = playbyplays


__all__ = ['NBAEvent', 'NBAGame', 'NBAPlayer', 'NBATeam']
