from datetime import timedelta
from json import JSONEncoder
from cached_property import cached_property
import pandas as pd

from statsnba.resources import StatsNBABoxscore, StatsNBAPlayByPlay
from statsnba.models.events import NBAEvent, _NBAEvent


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


class Team(object):
    def __init__(self, abbr, id):
        self.abbr = abbr
        self.id = id

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return 'Team({}, {})'.format(self.abbr, self.id)

    def __str__(self):
        return self.abbr

    def to_json(self):
        return {'abbr': self.abbr, 'id': self.id}

    @classmethod
    def from_boxscore(cls, team_boxscore):
        abbr = team_boxscore['TEAM_ABBREVIATION']
        id = team_boxscore['TEAM_ID']
        return Team(abbr, id)


class Player(object):
    STARTER_POSITION = 'starters'
    BENCH_POSITION   = 'bench'

    def __init__(self, name, id, team, start_position, **kwargs):
        self.name = name
        self.id = id
        self.team = team
        self.start_position = start_position

        self.__dict__.update(kwargs)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        """Check the equity between two players"""
        if self.id == other.id:
            return True
        else: return False

    def __cmp__(self, other):
        """This is not for sorting the players in a container object"""
        return cmp(self.name, other.name)

    def __repr__(self):
        return 'Player({}, {}, {})'.format(self.name, self.id, self.team.abbr)

    def __str__(self):
        return self.name

    def to_json(self):
        return {'name': self.name, 'id': self.id, 'team': self.team}

    @property
    def starter_or_bench(self):
        return self.start_position

    def is_starter(self):
        return True if self.start_position == Player.STARTER_POSITION else False

    @classmethod
    def from_player_stats(cls, player_stats):
        name = player_stats['PLAYER_NAME']
        id = player_stats['PLAYER_ID']
        team = Team(abbr=player_stats['TEAM_ABBREVIATION'],
                    id=player_stats['TEAM_ID'])
        start_position = Player.STARTER_POSITION if player_stats['START_POSITION'] else Player.BENCH_POSITION
        return Player(name=name, id=id, team=team, start_position=start_position)


class Matchup(object):
    def __init__(self, matchup_group):
        self.matchup_group = matchup_group
        self._df = pd.DataFrame([e.to_dict() for e in matchup_group])

    @classmethod
    def matchup_groups(cls, playbyplay):
        """Split the game's playbyplay into separate groups of matchups"""
        matchup = []
        for i, event in enumerate(playbyplay[:-1]):
            matchup.append(event)
            if event.players != playbyplay[i+1].players and playbyplay[i+2].event_type != 'substitution' :
                yield matchup
                matchup = []
        yield matchup

    @staticmethod
    def compute_boxscore(group, team):
        home_team = group.iloc[0].home_team.abbr
        away_team = group.iloc[0].away_team.abbr

        _home = group['team'] == home_team
        _away = group['team'] == away_team
        _team = locals()['_'+team]
        _opp_team = _home if team == 'away' else _away

        _before_ptd = group.iloc[0].home_score - group.iloc[0].away_score
        _after_ptd = group.iloc[-1].home_score - group.iloc[-1].away_score

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

        elapsed_time = (group.iloc[-1].overall_elapsed_time - group.iloc[0].overall_elapsed_time).seconds
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
        home_stats = Matchup.compute_boxscore(group, 'home')
        away_stats = Matchup.compute_boxscore(group, 'away')
        first_ev = self.matchup_group[0]
        last_ev = self.matchup_group[-1]
        # TODO Refactor this to be accessors on a Matchup instance
        return dict(
            start_id=first_ev.play_id,
            end_id=last_ev.play_id,
            home_players=sorted(list(first_ev.home_players)),
            away_players=sorted(list(first_ev.away_players)),
            home_stats=home_stats,
            away_stats=away_stats,
            home_start_score=first_ev.home_score,
            away_start_score=first_ev.away_score,
            home_end_score=last_ev.home_score,
            away_end_score=last_ev.away_score,
            point_difference=((last_ev.home_score - first_ev.home_score)
                              - (last_ev.away_score - first_ev.away_score)),
            elapsed_seconds=home_stats['elapsed_time'])


class Game(object):
    def __init__(self, game_id, boxscore=None, playbyplays=None):
        self.game_id = game_id
        self._boxscore = boxscore
        self._playbyplay = playbyplays
        if not self._boxscore:
            self._boxscore= StatsNBABoxscore.fetch_resource({'GameID': self.game_id})
        if not self._playbyplay:
            self._playbyplay = StatsNBAPlayByPlay.fetch_resource({'GameID': self.game_id})

    @classmethod
    def create_game(cls, game_id):
        boxscore= StatsNBABoxscore.fetch_resource({'GameID': game_id})
        pbps = StatsNBAPlayByPlay.fetch_resource({'GameID': game_id})
        return Game(game_id, boxscore, pbps)

    def to_json(self):
        fields = [
            'game_id', '_boxscore', '_playbyplay',
            'matchups',
            'home_team', 'away_team',
            'players', 'home_players', 'away_players',
            'home_bench', 'away_bench',
            'home_starters', 'away_starters',
            'game_length']
        return {k:getattr(self, k) for k in fields}

    def _get_playbyplay(self):
        """Return a cached copy of the playbyplay resultSet"""
        return self._playbyplay['resultSets']['PlayByPlay']

    @cached_property
    def playbyplay(self):
        pbps = []
        for i in range(len(self._get_playbyplay())):
            ev = NBAEvent(i, game=self)
            pbps.append(ev)
        pbps = _NBAEvent.update_game_players(pbps)
        return pbps

    @property
    def matchups(self):
        matchups = Matchup.matchup_groups(self.playbyplay)
        for m in iter(matchups):
            yield Matchup(m)

    # Below are properties of the game
    @cached_property
    def home_team(self):
        home_boxscore = StatsNBABoxscore.home_boxscore(self._boxscore)
        return Team.from_boxscore(home_boxscore)

    @cached_property
    def away_team(self):
        away_boxscore = StatsNBABoxscore.away_boxscore(self._boxscore)
        return Team.from_boxscore(away_boxscore)

    @cached_property
    def players(self):
        player_stats = StatsNBABoxscore.player_stats(self._boxscore)
        return set(map(lambda p: Player.from_player_stats(p), player_stats))

    @cached_property
    def home_players(self):
        return set([p for p in self.players if p.team == self.home_team])

    @cached_property
    def home_starters(self):
        return set([p for p in self.home_players if p.starter_or_bench=='starters'])

    @cached_property
    def home_bench(self):
        return set([p for p in self.home_players if p.starter_or_bench=='bench'])

    @cached_property
    def away_players(self):
        return set([p for p in self.players if p.team == self.away_team])

    @cached_property
    def away_starters(self):
        return set([p for p in self.away_players if p.starter_or_bench=='starters'])

    @cached_property
    def away_bench(self):
        return set([p for p in self.away_players if p.starter_or_bench=='bench'])

    @cached_property
    def game_length(self):
        from datetime import timedelta
        period = int(self._playbyplay['resultSets']['PlayByPlay'][-1]['PERIOD'])
        if period > 4:
            return timedelta(minutes=((period-4) * 5 + 12 * 4))
        else:
            return timedelta(minutes=48)

    def find_players_in_range(self, start_range, end_range):
        range_boxscore = StatsNBABoxscore.find_boxscore_in_range(self.game_id, start_range, end_range)
        return set(map(Player.from_player_stats, range_boxscore['resultSets']['PlayerStats']))

    def _find_player(self, player_name):
        """use player's name and team to find the player"""
        for p in self.players:
            if p.name == player_name:
                return p
        raise Exception('%s is not found in this game' % player_name)
