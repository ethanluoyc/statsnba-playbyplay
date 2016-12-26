from datetime import timedelta
from json import JSONEncoder

from cached_property import cached_property
from inflection import camelize

from statsnba.api import Api
import gevent

_async_fetch = True

__all__ = ['Game', 'Player', 'Team', 'Matchup']


# noinspection PyUnresolvedReferences
class Model(object):
    """Base class for other models such as Team and Player, used to enforce
    existence of some fields"""
    _required_fields = []

    def __init__(self, model_dict=None, **kwargs):
        """All attributes are CamelCased"""
        if isinstance(model_dict, dict):
            try:
                assert not kwargs
            except AssertionError:
                raise AssertionError(
                    'When using a dict to instantiate {0}, no other keywords should be supplied'.format(
                        self.__class__))
            else:
                kws = model_dict
        elif model_dict is None:
            kws = kwargs
        else:
            raise TypeError("Invalid arguments supplied")

        for key, value in kws.items():
            setattr(self, camelize(key.lower()),
                    value)  # Maybe just strip all non-required fields?
        self._validate_fields()

    def _validate_fields(self):
        for field in self._required_fields:
            if not getattr(self, field, None):
                raise TypeError('{0} is required by {1}'.format(
                    field, self.__class__.__name__))

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
        return 'Player({}, {}, {})'.format(self.PlayerName, self.PlayerId,
                                           repr(self.Team))

    def __str__(self):
        return self.PlayerName

    @property
    def starter_or_bench(self):
        return self.STARTER_POSITION if self.is_starter(
        ) else self.BENCH_POSITION

    def is_starter(self):
        return True if self.StartPosition else False


class MatchupGroupException(Exception):
    """Raised when it fails to locate a matchup"""
    pass


class Matchup(object):
    """A matchup is simply an abstraction over a list events identified
    by the players on the court, with some additional properties
    that are specific to matchups. (e.g. the HomePlayers and AwayPlayers for
    this matchup). The wrapping is really simple, so if you are confused, feel
    free to read the source code.

    >>> game = Game('0020900292')
    >>> matchups = game.Matchups
    >>> first_matchup = matchups[0] # The first matchup in game.
    >>> first_event_of_first_matchup = first_matchup[0]

    statsnba-playbyplay calculates the statistics of the two opposing
    teams in a particular matchup. They are located in matchup.Boxscore.
    You can query those statistics by

    >>> matchup.Boxscore.HomeTeamStats # for home team.
    >>> matchup.Boxscore.AwayTeamStats # away team.

    """

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
        try:
            for i, event in enumerate(playbyplay[:-1]):
                matchup.append(event)
                if event.OnCourtPlayers != playbyplay[i + 1].OnCourtPlayers \
                   and playbyplay[i + 2].EventType != EventType.Substitution:
                    yield matchup
                    matchup = []
            yield matchup
        except Exception:
            raise MatchupGroupException()

    @property
    def HomePlayers(self):
        return self.matchup_group[0].HomePlayers

    @property
    def AwayPlayers(self):
        return self.matchup_group[0].AwayPlayers

    @property
    def Players(self):
        return self.HomePlayers | self.AwayPlayers

    @property
    def GameId(self):
        return self.matchup_group[0].GameId

    def __getitem__(self, key):
        return self.matchup_group[key]


class EmptyPlayByPlayException(Exception):
    pass


class Game(object):
    """An object containing all information for a game in a season.

    For those people working on basketball analytics, this is usually the most
    frequently used class for your work.

    The way you use this class is to instantiate it with a game-id (those used to
    identify a particular game from the official stats.nba.com website)

    Note: the game-id is a str of length 10, not int.

    >>> game = Game('0020900292')
    >>> game.GameId
    '0020900292'

    a Game in statsnba-playbyplay is the root of a hierachy of objects
    associated with information for a given game. In particular, it has the
    following hierachy

    Game
    |_ GameId
    |_ Team
       |_ HomeTeam
       |_ AwayTeam
    |_ Players
       |_ HomePlayers
          |_ HomeBench
          |_ HomeStarters
       |_ AwayPlayers
          |_ AwayBench
          |_ AwayStarters
    |_ PlayByPlay
    |_ Matchups

    For how you access these fields and what they return, see each public
    methods' documentation.

    """

    def __init__(self, game_id, boxscore=None, playbyplays=None):
        self.game_id = game_id
        self._boxscore = boxscore
        self._playbyplay = playbyplays
        global _async_fetch
        if not self._boxscore or not self._playbyplay:
            api = Api()
            if not _async_fetch:
                self._boxscore = api.GetBoxscore(game_id)
                self._playbyplay = api.GetPlayByPlay(game_id)
                self._boxscore_summary = api.GetBoxscoreSummary(game_id)
            else:
                box_job = gevent.spawn(api.GetBoxscore, game_id)
                pbp_job = gevent.spawn(api.GetPlayByPlay, game_id)
                bs_job = gevent.spawn(api.GetBoxscoreSummary, game_id)
                gevent.joinall([box_job, pbp_job, bs_job])

                self._boxscore = box_job.value
                self._playbyplay = pbp_job.value
                self._boxscore_summary = bs_job.value

        self._matchups = None

    def _get_playbyplay(self):
        """Return a cached copy of the playbyplay resultSet"""
        return self._playbyplay['resultSets']['PlayByPlay']

    def __repr__(self):
        return 'Game({})'.format(self.game_id)

    @property
    def GameId(self):
        """The game-id of the game"""
        return self.game_id

    @property
    def PlayByPlay(self):
        """the playbyplay of this game.
        The playbyplay of a game is just the list of events that happen during
        the course of this game.
        Returns: a list of `Event`.
        """
        # TODO refactor
        pbps = []
        for i in range(len(self._get_playbyplay())):
            ev = Event(i, Game=self)
            pbps.append(ev)
        if len(pbps) == 0:
            raise EmptyPlayByPlayException(
                'the playbyplay is empty for {}'.format(repr(self)))
        pbps = update_game_players(pbps)
        return pbps

    @property
    def Matchups(self):
        """a list of matchups for the game.
        A matchup is a segment of the playbyplay where the on court players
        stay the same. This is frequently used in calculation of per-matchup
        statitics such as APM or RAPM.

        Returns: A list of `Matchup`.
        """
        if self._matchups:
            return self._matchups
        matchups_grps = Matchup.MatchupGroups(self.PlayByPlay)
        matchups = [Matchup(m) for m in iter(matchups_grps)]
        self._matchups = matchups
        return matchups

    _HOME_INDEX = 1
    _AWAY_INDEX = 0

    # Below are properties of the game
    @property
    def _HomeBoxscore(self):
        home_team_id = self._boxscore_summary['resultSets']['GameSummary'][0][
            "HOME_TEAM_ID"]
        if self._boxscore['resultSets']['TeamStats'][0][
                'TEAM_ID'] == home_team_id:
            return self._boxscore['resultSets']['TeamStats'][0]
        else:
            return self._boxscore['resultSets']['TeamStats'][1]

    @property
    def _AwayBoxscore(self):
        away_team_id = self._boxscore_summary['resultSets']['GameSummary'][0][
            "VISITOR_TEAM_ID"]
        if self._boxscore['resultSets']['TeamStats'][0][
                'TEAM_ID'] == away_team_id:
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
        return set(
            [p for p in self.HomePlayers if p.starter_or_bench == 'starters'])

    @cached_property
    def HomeBench(self):
        return set(
            [p for p in self.HomePlayers if p.starter_or_bench == 'bench'])

    @cached_property
    def AwayPlayers(self):
        return set([p for p in self.Players if p.Team == self.AwayTeam])

    @cached_property
    def AwayStarters(self):
        return set(
            [p for p in self.AwayPlayers if p.starter_or_bench == 'starters'])

    @cached_property
    def AwayBench(self):
        return set(
            [p for p in self.AwayPlayers if p.starter_or_bench == 'bench'])

    @cached_property
    def GameLength(self):
        """The length of the game, 48 minutes for a 4 period game with no overtime,
        5 minutes more for every one more period.
        """
        from datetime import timedelta
        period = int(self._playbyplay['resultSets']['PlayByPlay'][-1][
            'PERIOD'])
        if period > 4:
            return timedelta(minutes=((period - 4) * 5 + 12 * 4))
        else:
            return timedelta(minutes=48)

    def FindPlayersInRange(self, start_range, end_range):
        range_boxscore = self._find_boxscore_in_range(self.game_id,
                                                      start_range, end_range)
        return set(map(lambda p: Player(p), range_boxscore['resultSets'][
            'PlayerStats']))

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
