from datetime import timedelta
from json import JSONEncoder

from cached_property import cached_property
from inflection import camelize

from statsnba.api import Api


class GameEncoder(JSONEncoder):
    """Used to encode a game object to a JSON object"""

    def default(self, o):
        if hasattr(o, 'to_json'):
            return getattr(o, 'to_json')()
        elif isinstance(o, set):
            return sorted(list(o))
        elif isinstance(o, timedelta):
            return o.seconds
        # Convert generators to list
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder().default(o)


# noinspection PyUnresolvedReferences
class Model(object):
    """Base class for other models such as Team and Player, used to enforce existence of some fields"""
    _required_fields = []

    def __init__(self, model_dict=None, **kwargs):
        """All attributes are CamelCased"""
        if isinstance(model_dict, dict):
            try:
                assert not kwargs
            except AssertionError:
                raise AssertionError(
                    'When using a dict to instantiate {0}, no other keywords should be supplied'.format(self.__class__))
            else:
                kws = model_dict
        elif model_dict is None:
            kws = kwargs
        else:
            raise TypeError("Invalid arguments supplied")

        for key, value in kws.items():
            setattr(self, camelize(key.lower()), value)  # Maybe just strip all non-required fields?
        self._validate_fields()

    def _validate_fields(self):
        for field in self._required_fields:
            if not getattr(self, field, None):
                raise TypeError('{0} is required by {1}'.format(field, self.__class__.__name__))

    def ToDict(self):
        return {k: getattr(self, k) for k in self._required_fields}


# noinspection PyUnresolvedReferences
class Team(Model):
    _required_fields = ['TeamAbbreviation', 'TeamId']

    def __eq__(self, other):
        return self.TeamId == other.TeamId

    def __repr__(self):
        return 'Team({}, {})'.format(self.TeamAbbreviation, self.TeamId)

    def __str__(self):
        return self.TeamName


# noinspection PyUnresolvedReferences
class Player(Model):
    STARTER_POSITION = 'starters'
    BENCH_POSITION = 'bench'
    _required_fields = ['PlayerId', 'PlayerName', 'Team']

    def __init__(self, stats_dict=None, **kwargs):
        stats_dict = stats_dict.copy()
        team_kwargs = {}
        for field in stats_dict.keys():
            if field.startswith('TEAM_'):
                team_kwargs[field] = stats_dict.pop(field)
        self.Team = Team(**team_kwargs)
        super(Player, self).__init__(stats_dict)

    def __hash__(self):
        return hash(self.Team.TeamId)

    def __eq__(self, other):
        """Check the equity between two players"""
        if self.PlayerId == other.PlayerId:
            return True
        return False

    def __cmp__(self, other):
        """This is not for sorting the players in a container object"""
        return cmp(self.PlayerName, other.PlayerName)

    def __repr__(self):
        return 'Player({}, {}, {})'.format(self.PlayerName,
                                           self.PlayerId, repr(self.Team))

    def __str__(self):
        return self.PlayerName

    @property
    def starter_or_bench(self):
        return self.STARTER_POSITION if self.is_starter() else self.BENCH_POSITION

    def is_starter(self):
        return True if self.StartPosition else False


class Matchup(object):
    """A matchup is a collection of events identified by the players on the court."""

    def __init__(self, matchup_group):
        self.matchup_group = matchup_group
        self.Boxscore = BoxscoreStats(matchup_group)

    @classmethod
    def MatchupGroups(cls, playbyplay):
        """Split the game's playbyplay into separate groups of matchups

            Returns:
                matchup_lst (list): list of Events in a group
        """
        matchup = []
        for i, event in enumerate(playbyplay[:-1]):
            matchup.append(event)
            if event.OnCourtPlayers != playbyplay[i + 1].OnCourtPlayers \
                and playbyplay[i + 2].EventType != EventType.Substitution:
                yield matchup
                matchup = []
        yield matchup


class Game(object):
    def __init__(self, game_id, boxscore=None, playbyplays=None):
        self.game_id = game_id
        self._boxscore = boxscore
        self._playbyplay = playbyplays
        if not self._boxscore or not self._playbyplay:
            api = Api()
            self._boxscore = api.GetBoxscore(game_id)
            self._playbyplay = api.GetPlayByPlay(game_id)
            self._boxscore_summary = api.GetBoxscoreSummary(game_id)

    def _get_playbyplay(self):
        """Return a cached copy of the playbyplay resultSet"""
        return self._playbyplay['resultSets']['PlayByPlay']

    @cached_property
    def GameId(self):
        return self.game_id

    @cached_property
    def PlayByPlay(self):
        # TODO refactor
        pbps = []
        for i in range(len(self._get_playbyplay())):
            ev = Event(i, Game=self)
            pbps.append(ev)
        pbps = update_game_players(pbps)
        return pbps

    @property
    def Matchups(self):
        matchups = Matchup.MatchupGroups(self.PlayByPlay)
        for m in iter(matchups):
            yield Matchup(m)

    _HOME_INDEX = 1
    _AWAY_INDEX = 0

    # Below are properties of the game
    @property
    def _HomeBoxscore(self):
        home_team_id = self._boxscore_summary['resultSets']['GameSummary'][0]["HOME_TEAM_ID"]
        if self._boxscore['resultSets']['TeamStats'][0]['TEAM_ID'] == home_team_id:
            return self._boxscore['resultSets']['TeamStats'][0]
        else:
            return self._boxscore['resultSets']['TeamStats'][1]

    @property
    def _AwayBoxscore(self):
        away_team_id = self._boxscore_summary['resultSets']['GameSummary'][0]["VISITOR_TEAM_ID"]
        if self._boxscore['resultSets']['TeamStats'][0]['TEAM_ID'] == away_team_id:
            return self._boxscore['resultSets']['TeamStats'][0]
        else:
            return self._boxscore['resultSets']['TeamStats'][1]

    @cached_property
    def HomeTeam(self):
        return Team(self._HomeBoxscore)

    @cached_property
    def AwayTeam(self):
        return Team(self._AwayBoxscore)

    @property
    def _PlayerStats(self):
        return self._boxscore['resultSets']['PlayerStats']

    @cached_property
    def Players(self):
        """Return a set of players"""
        return set(map(lambda p: Player(p), self._PlayerStats))

    @cached_property
    def HomePlayers(self):
        return set([p for p in self.Players if p.Team == self.HomeTeam])

    @cached_property
    def HomeStarters(self):
        return set([p for p in self.HomePlayers if p.starter_or_bench == 'starters'])

    @cached_property
    def HomeBench(self):
        return set([p for p in self.HomePlayers if p.starter_or_bench == 'bench'])

    @cached_property
    def AwayPlayers(self):
        return set([p for p in self.Players if p.Team == self.AwayTeam])

    @cached_property
    def AwayStarters(self):
        return set([p for p in self.AwayPlayers if p.starter_or_bench == 'starters'])

    @cached_property
    def AwayBench(self):
        return set([p for p in self.AwayPlayers if p.starter_or_bench == 'bench'])

    @cached_property
    def GameLength(self):
        from datetime import timedelta
        period = int(self._playbyplay['resultSets']['PlayByPlay'][-1]['PERIOD'])
        if period > 4:
            return timedelta(minutes=((period - 4) * 5 + 12 * 4))
        else:
            return timedelta(minutes=48)

    def FindPlayersInRange(self, start_range, end_range):
        range_boxscore = self._find_boxscore_in_range(self.game_id, start_range, end_range)
        return set(map(lambda p: Player(p), range_boxscore['resultSets']['PlayerStats']))

    @staticmethod
    def _find_boxscore_in_range(game_id, start_range, end_range):
        api = Api()
        return api.GetBoxscore(GameID=game_id,
                               StartRange=start_range,
                               EndRange=end_range,
                               RangeType='2')


from statsnba.models.events import Event, update_game_players
from .events import EventType
from statsnba.models.stats import BoxscoreStats

