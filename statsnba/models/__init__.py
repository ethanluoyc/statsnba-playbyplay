from datetime import timedelta
from json import JSONEncoder

import pandas as pd
from cached_property import cached_property
from inflection import camelize

from statsnba.api import Api
from statsnba.resources import StatsNBABoxscore


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
            setattr(self, camelize(key.lower()), value)
        self._validate_fields()

    def _validate_fields(self):
        for field in self._required_fields:
            if not getattr(self, field, None):
                raise TypeError('{0} is required by {1}'.format(field, self.__class__.__name__))


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
        self._df = pd.DataFrame([e.ToDict() for e in matchup_group])

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

    @staticmethod
    def ComputeBoxscore(group, team):
        home_team = group.iloc[0].HomeTeam.abbr
        away_team = group.iloc[0].AwayTeam.abbr

        _home = group['team'] == home_team
        _away = group['team'] == away_team
        _team = locals()['_' + team]
        _opp_team = _home if team == 'away' else _away

        _before_ptd = group.iloc[0].HomeScore - group.iloc[0].AwayScore
        _after_ptd = group.iloc[-1].HomeScore - group.iloc[-1].AwayScore

        FGM = ((group['event_type'] == 'shot made'))
        FGA = (FGM | (group['event_type'] == 'shot missed'))
        FG3M = FGM & (group['type'] == '3 points')
        FG3A = FGA & (group['type'] == '3 points')
        OREB = ((group['event_type'] == 'offensive rebound'))
        DREB = ((group['event_type'] == 'defensive rebound'))
        REB = OREB | DREB
        FTM = (group['event_type'] == 'free throw') & (group['result'] == 'made')
        FTA = (group['event_type'] == 'free throw')
        _FT_GROUPS = ((group['event_type'] == 'free throw') & (group['num'] == 1))

        AST = group['assist'].notnull()
        BLK = group['block'].notnull()
        TOV = ((group['event_type'] == 'turnover'))
        STL = group['steal'].notnull() & TOV
        PF = ((group['event_type'] == 'foul')) | ((group['event_type'] == 'violation'))

        elapsed_time = (group.iloc[-1].OverallElapsedTime - group.iloc[0].OverallElapsedTime).seconds
        possessions = len(group[(FGA & _team)]) \
                      - len(group[OREB & _team]) \
                      + len(group[TOV & _team]) \
                      + len(group[_FT_GROUPS & _team])

        _stats = {}
        for k, v in locals().items():
            if isinstance(v, pd.Series) and not k.startswith('_'):
                _stats[k] = len(group[v & _team])
            elif not k.startswith('_') and k not in ['group', 'team']:
                _stats[k] = v if isinstance(v, int) or isinstance(v, float) else str(v)
        _stats['STL'] = len(group[STL & _opp_team])  # steal is from the opposite
        _stats['BLK'] = len(group[BLK & _opp_team])  # steal is from the opposite
        return _stats

    def to_json(self):
        group = self._df
        home_stats = Matchup.ComputeBoxscore(group, 'home')
        away_stats = Matchup.ComputeBoxscore(group, 'away')
        first_ev = self.matchup_group[0]
        last_ev = self.matchup_group[-1]
        # TODO Refactor this to be accessors on a Matchup instance
        return dict(
            start_id=first_ev.play_id,
            end_id=last_ev.play_id,
            home_players=sorted(list(first_ev.HomePlayers)),
            away_players=sorted(list(first_ev.AwayPlayers)),
            home_stats=home_stats,
            away_stats=away_stats,
            home_start_score=first_ev.HomeScore,
            away_start_score=first_ev.AwayScore,
            home_end_score=last_ev.HomeScore,
            away_end_score=last_ev.AwayScore,
            point_difference=((last_ev.HomeScore - first_ev.HomeScore)
                              - (last_ev.AwayScore - first_ev.AwayScore)),
            elapsed_seconds=home_stats['elapsed_time'])


class Game(object):
    def __init__(self, game_id, boxscore=None, playbyplays=None):
        self.game_id = game_id
        self._boxscore = boxscore
        self._playbyplay = playbyplays
        if not self._boxscore or not self._playbyplay:
            api = Api()
            self._boxscore = api.GetBoxscore(game_id)
            self._playbyplay = api.GetPlayByPlay(game_id)

    def to_json(self):
        fields = [
            'game_id', '_boxscore', '_playbyplay',
            'matchups',
            'home_team', 'away_team',
            'players', 'home_players', 'away_players',
            'home_bench', 'away_bench',
            'home_starters', 'away_starters',
            'game_length']
        return {k: getattr(self, k) for k in fields}

    def _get_playbyplay(self):
        """Return a cached copy of the playbyplay resultSet"""
        return self._playbyplay['resultSets']['PlayByPlay']

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

    _HOME_INDEX = 0
    _AWAY_INDEX = 1

    # Below are properties of the game
    @property
    def _HomeBoxscore(self):
        return self._boxscore['resultSets']['TeamStats'][Game._HOME_INDEX]

    @property
    def _AwayBoxscore(self):
        return self._boxscore['resultSets']['TeamStats'][Game._AWAY_INDEX]

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
        range_boxscore = StatsNBABoxscore.find_boxscore_in_range(self.game_id, start_range, end_range)
        return set(map(lambda p: Player(p), range_boxscore['resultSets']['PlayerStats']))


from statsnba.models.events import Event, update_game_players
from .events import EventType
