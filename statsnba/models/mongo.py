# This module wraps up our model definition and adds additional functionality for interacting with MongoDB
from mongoengine import *

from statsnba.models.events import NBAEvent
from statsnba.resources import StatsNBABoxscore, StatsNBAPlayByPlay
from cached_property import cached_property
import pandas as pd
from mongoengine.context_managers import switch_db

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

    @classmethod
    def from_boxscore(cls, team_boxscore):
        abbr = team_boxscore['TEAM_ABBREVIATION']
        id = team_boxscore['TEAM_ID']
        return Team(abbr, id)


# these are always only available within the context of a game
class Event(EmbeddedDocument):
    home_player_ids = SortedListField(IntField())   # TODO why inconsistent with EmbeddedDocumentListField?
    away_player_ids = SortedListField(IntField())   # these needs to be updated by querying the API
    data = DictField()                             # information about the event (playbyplay)

    @staticmethod
    def update_players(events):
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


class Gamelog(DynamicDocument):
    GAME_ID = StringField()
    MATCHUP = StringField(unique_with='GAME_ID')  # two fields that help to ensure unique
    @classmethod
    def create_season_gamelogs(cls, season):
        from statsnba.resources import StatsNBAGamelog
        res = StatsNBAGamelog.fetch_resource({'Season': season})
        for gamelog in res['resultSets']['LeagueGameLog']:
            Gamelog(**gamelog).save()

class Game(Document):
    game_id = StringField(required=True, unique=True)
    _playbyplay = DictField()                            # fetched from stats.nba.com
    _boxscore = DictField()                              # fetched from stats.nba.com
    home_gamelog = ReferenceField(Gamelog, require=True)
    away_gamelog = ReferenceField(Gamelog, require=True)

    @classmethod
    def create_game(cls, game_id):
        boxscore= StatsNBABoxscore.fetch_resource({'GameID': game_id})
        pbps = StatsNBAPlayByPlay.fetch_resource({'GameID': game_id})

        connect(host='mongodb://localhost:27017/statsnba', connect=False)
        # About why using a context mgr `see https://jira.mongodb.org/browse/PYTHON-1016`
        # also see https://emptysqua.re/blog/getaddrinfo-deadlock/
        with switch_db(Gamelog, 'default') as Gamelog_alias:
            home_gamelog = Gamelog_alias.objects(GAME_ID=game_id, MATCHUP__contains='vs.').get()
            away_gamelog = Gamelog_alias.objects(GAME_ID=game_id, MATCHUP__contains='@').get()
        game = Game(game_id=game_id, _playbyplay=pbps, _boxscore=boxscore, home_gamelog=home_gamelog, away_gamelog=away_gamelog)
        game.save()


        return game

    @cached_property
    def playbyplay(self):
        pbps = []
        for i in range(len(self._get_playbyplay)):
            ev = NBAEvent(i, game=self)
            pbps.append(ev)
        pbps = Event.update_players(pbps)
        return pbps

    @cached_property
    def _get_playbyplay(self):
        """Return a cached copy of the playbyplay resultSet"""
        return self._playbyplay['resultSets']['PlayByPlay']

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




class Matchup(Document):
    game = ReferenceField(Game, required=True)
    home_stats = DictField(required=True)                             # various metrics for that matchup
    away_stats = DictField(required=True)                             # various metrics for that matchup
    home_player_ids = SortedListField(IntField(), required=True)
    away_player_ids = SortedListField(IntField(), required=True)

    start_id = IntField(required=True)
    end_id = IntField(required=True)

    home_start_score = IntField()
    away_start_score = IntField()
    home_end_score = IntField()
    away_end_score = IntField()
    point_difference = IntField()
    elapsed_time = IntField()

    @classmethod
    def create_matchups(cls, playbyplay):
        """Matchups are created by aggregating the events based on their players on court"""
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
        for k,v in locals().items():
            if isinstance(v, pd.Series) and not k.startswith('_'):
                _stats[k] = len(group[v & _team])
            elif not k.startswith('_') and k not in ['group', 'team']:
                _stats[k] = v if isinstance(v, int) or isinstance(v, float) else str(v)
        _stats['STL'] = len(group[STL & _opp_team]) # steal is from the opposite
        _stats['BLK'] = len(group[BLK & _opp_team]) # steal is from the opposite
        return _stats


class Player(object):
    STARTER_POSITION = 'starters'
    BENCH_POSITION   = 'bench'

    def __init__(self, name, id, team, **kwargs):
        self.name = name
        self.id = id
        self.team = team

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


if __name__ == '__main__':
    pass
