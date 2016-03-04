from statsnba import config
from pymongo import MongoClient
from statsnba.parse import parse


class MongoTeam(object):
    def __init__(self):
        pass

    def __eq__(self, other_team):
        pass


class MongoPlayer(object):
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


class MongoEvent(object):
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
        raise NotImplementedError

    @property
    def away_player(self):
        raise NotImplementedError

    def update_players(self, players):
        self._players = self._players | players


class MongoGame(object):
    def __init__(self, game_id):
        self._db = MongoClient(config['mongodb']['uri'])[config['mongodb']['database']]
        self._boxscore = self._db.boxscoretraditionalv2.find_one({'parameters.GameID': game_id})
        self._pbp = self._db.playbyplay.find_one({'parameters.GameID': game_id})
        self._players = set(map(lambda p: MongoPlayer(player_stats=p), self._boxscore['resultSets']['PlayerStats']))

    def __del__(self):
        self._db.close()

    def find_one_record(self):
        """If there is not a record, then fetch it"""
        pass

    def fetch_record(self):
        pass

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
        """Playbyplay is the collection of events"""
        on_court_players = self.home_starters | self.away_starters
        on_court_players_initial = on_court_players.copy()
        pbp = []

        for i, p in enumerate(self._pbp['resultSets']['PlayByPlay']):
            ev = MongoEvent(p, game=self)
            to_update_floor_players = False
            if ev.period > MongoEvent(self._pbp['resultSets']['PlayByPlay'][i-1]).period:
                # this conditional comes first otherwise it will result in player not found
                # TODO
                to_update_floor_players = True
            elif ev.event_type == 'substitution':
                # TODO
                start_range = (ev.period - 1) * 12  * 600 + 1 # hacky
                end_range = (ev.period - 1) * 12 * 600 + 7200 - ev.current_time.seconds * 10
                on_court_player = self.update_floor_players(start_range, end_range)
                on_court_players.remove(self.find_player(ev.left))  # TODO got error
                on_court_players.add(self.find_player(ev.entered))
            ev.update_players(on_court_players)
            pbp.append(ev)
        return pbp

    def find_floor_player(self, start_range, end_range):
        """this is to update the players on the floor, used to find players on the court for every play"""
        players = set([])
        return players


    def boxscore_in_range(self, start_range, end_range):
        pass

    def find_player(self, player_name):
        """use player's name and team to find the player"""
        for p in self._players:
            if p.name == player_name:
                return p
        raise Exception('%s is not found in this game' % player_name)
