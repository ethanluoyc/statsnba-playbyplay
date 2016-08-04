import re
import logging
from cached_property import cached_property
from statsnba.models import Player
from enum import Enum

logger = logging.getLogger(__name__)


def parse_player(num, event_stats):
    """Parse the num'th player from event_dict, return None if the player is None
        :param num: (int) the position of the player to parse
        :param event_stats: the dict for parsing
    """
    # TODO parse PersonType
    pat = re.compile('^PLAYER{0}_.+'.format(num))
    pat_team = re.compile('^PLAYER{0}_TEAM_.+'.format(num))
    kwargs = {}
    for k, v in event_stats.items():
        if pat.match(k):
            if pat_team.match(k):
                kwargs[re.sub(r'PLAYER\d_', '', k)] = v
            else:
                kwargs[re.sub(r'\d', '', k)] = v
    if not kwargs['PLAYER_NAME']:
        return None
    return Player(kwargs)


def limit_to_types(eventtype_or_lst):
    def real_dec(func):
        def limit_eventtype(self):
            if not isinstance(eventtype_or_lst, list):
                permitted = [eventtype_or_lst]
            else:
                permitted = eventtype_or_lst
            permitted = [EventType[item] for item in permitted]
            if self.EventType in permitted:
                return func(self)
            return None
        return limit_eventtype
    return real_dec


class EventType(Enum):
    """The EventType as identified by EVENTMSGTYPE from the PlayByPlay dict"""
    ShotMade = 1
    ShotMiss = 2
    FreeThrow = 3
    Rebound = 4
    Turnover = 5
    Foul = 6
    Violation = 7
    Substitution = 8
    Timeout = 9
    JumpBall = 10
    Ejection = 11
    StartOfPeriod = 12
    EndOfPeriod = 13
    Unknown = -1


# noinspection PyPep8Naming
class Event(object):
    Fields = ['GameId', 'EventType', 'Type', 'PlayId', 'Description',
              'Team', 'HomeTeam', 'AwayTeam',
              'Player', 'HomePlayers', 'AwayPlayers',
              'Period', 'PeriodLength', 'PeriodElapsedTime', 'PeriodRemainingTime',
              'OverallLength', 'OverallElapsedTime', 'OverallRemainingTime',
              'HomeScore', 'AwayScore', 'Points',
              'Block',                             # ShotMade ShotMiss
              'Assist',                            # ShotMade ShotMiss
              'Result',                            # ShotMade ShotMiss FreeThrow
              'Steal',                             # Turnover
              'Home', 'Away', 'Possession',        # JumpBall
              'Left', 'Entered',                   # Substitution
              'Num', 'OutOf']                      # FreeThrow

    def __init__(self, stats_dict_or_idx, Game=None):
        if isinstance(stats_dict_or_idx, int):
            event_dict = Game._get_playbyplay()[stats_dict_or_idx]
        else:
            event_dict = stats_dict_or_idx
        self._Game = Game
        self._Players = set()
        self._EventDict = event_dict
        self._EventNum = Game._get_playbyplay().index(event_dict)

    def __repr__(self):
        return '<{0},{1}>'.format(self.EventType.name, self._EventNum)

    def ToDict(self):
        return {field: getattr(self, field) for field in self.Fields}

    @cached_property
    def GameId(self):
        return self._Game.GameId

    @cached_property
    def EventType(self):
        """
            Returns:
                event_type (EventType): the event_type of the NBA event.
        """
        type_num = self._EventDict['EVENTMSGTYPE']
        try:
            return EventType(type_num)
        except ValueError:
            return EventType.Unknown

    @cached_property
    def Type(self):
        if self.EventType in [EventType.ShotMiss, EventType.ShotMade]:
            data = self._EventDict
            descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                            data['NEUTRALDESCRIPTION']]
            for des in descriptions:
                if des is None:
                    des = ''
                if re.search('3PT', des):
                    return '3 points'
        if self.EventType is EventType.Rebound:
            prev_event = Event(self._EventNum - 1, Game=self._Game)
            while prev_event.EventType not in [EventType.ShotMade, EventType.ShotMiss,
                                         EventType.FreeThrow, EventType.JumpBall]:
                event_stats_idx = prev_event._EventNum - 1
                assert event_stats_idx > 0
                prev_event = Event(event_stats_idx, Game=self._Game)
            if (prev_event.EventType is EventType.JumpBall
                and prev_event.Possession.Team == self.Team) or prev_event.Team == self.Team:
                event_type = 'offensive'
            else:
                event_type = 'defensive'
            return event_type

    @property
    def PlayId(self):
        return self._EventDict['EVENTNUM']

    @property
    def Description(self):
        # TODO implement this
        return None

    # Team related
    @property
    @limit_to_types(['ShotMade', 'ShotMiss', 'FreeThrow', 'Rebound', 'Substitution', 'Turnover',
                     'Foul', 'Violation', 'Timeout', 'Ejection'])
    def Team(self):
        if self.EventType is EventType.Rebound:
            if self._EventDict['HOMEDESCRIPTION']:
                return self.HomeTeam
            elif self._EventDict['VISITORDESCRIPTION']:
                return self.AwayTeam
        if self._EventDict['PLAYER1_NAME']:
            return parse_player(1, self._EventDict).Team
        return None

    @property
    def HomeTeam(self):
        return self._Game.HomeTeam

    @property
    def AwayTeam(self):
        return self._Game.AwayTeam

    # Player related
    @property
    @limit_to_types(['ShotMade', 'ShotMiss', 'FreeThrow', 'Rebound', 'Substitution', 'Turnover',
                     'Foul', 'Violation', 'Timeout', 'Ejection'])
    def Player(self):
        return parse_player(1, self._EventDict)

    @property
    def OnCourtPlayers(self):
        if self._Players:
            return self._Players
        else:
            raise Exception('You have not updated the players')

    @property
    def HomePlayers(self):
        return set([p for p in self._Players if p.Team == self.HomeTeam])

    @property
    def AwayPlayers(self):
        return set([p for p in self._Players if p.Team == self.AwayTeam])

    def _UpdatePlayers(self, players):
        self._Players = self._Players | players

    # Period related
    @property
    def Period(self):
        return int(self._EventDict['PERIOD'])

    @cached_property
    def PeriodLength(self):
        from datetime import timedelta
        period_time_total = timedelta(minutes=5) if int(self.Period) > 4 else timedelta(minutes=12)

        return period_time_total

    @staticmethod
    def _ParsePCTimeString(timestring):
        from datetime import datetime, timedelta
        time = datetime.strptime(timestring, '%M:%S')  # parse minutes like this '10:29'
        return timedelta(minutes=time.minute, seconds=time.second)

    @cached_property
    def PeriodElapsedTime(self):
        return self.PeriodLength - self._ParsePCTimeString(self._EventDict['PCTIMESTRING'])

    @cached_property
    def PeriodRemainingTime(self):
        return self._ParsePCTimeString(self._EventDict['PCTIMESTRING'])

    @cached_property
    def OverallLength(self):
        return self._Game.GameLength

    @cached_property
    def OverallElapsedTime(self):
        from datetime import timedelta
        if self.Period > 4:
            return timedelta(minutes=(int(self.Period) - 5) * 5 + 12 * 4) + self.PeriodElapsedTime
        else:
            return timedelta(minutes=(int(self.Period) - 1) * 12) + self.PeriodElapsedTime

    @cached_property
    def OverallRemainingTime(self):
        return self.OverallLength - self.OverallElapsedTime

    @staticmethod
    def _Score(data, home_or_away):
        if not data['SCORE']:
            return None
        score = data['SCORE'].split('-')
        if home_or_away == 'home':
            group = 1
        elif home_or_away == 'away':
            group = 2
        else:
            raise Exception('You specified an unknwon flag')
        return int(score[group - 1].strip())

    # Score related
    # TODO refactor this
    @cached_property
    def HomeScore(self):
        score = self._Score(self._EventDict, 'home')
        stats_idx = self._EventNum
        while not score:
            if stats_idx == 0:
                return 0
            else:
                stats_idx -= 1
                stats = self._Game._get_playbyplay()[stats_idx]
                score = self._Score(stats, 'home')
        return score

    @cached_property
    def AwayScore(self):
        score = self._Score(self._EventDict, 'away')
        stats_idx = self._EventNum
        while not score:
            if stats_idx == 0:
                return 0
            else:
                stats_idx -= 1
                stats = self._Game._get_playbyplay()[stats_idx]
                score = self._Score(stats, 'away')
        return score

    # Properties limited to certain EventType
    @cached_property
    @limit_to_types(['ShotMade', 'ShotMiss', 'FreeThrow'])
    def Points(self):
        data = self._EventDict
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
        if self.Result == 'missed':
            pts = 0
        return pts

    @cached_property
    @limit_to_types(['ShotMade', 'ShotMiss'])
    def Block(self):
        return parse_player(3, self._EventDict)

    @cached_property
    @limit_to_types(['ShotMade', 'ShotMiss'])
    def Assist(self):
        return parse_player(2, self._EventDict)

    @cached_property
    @limit_to_types(['ShotMade', 'ShotMiss', 'FreeThrow'])
    def Result(self):
        if self.EventType is EventType.FreeThrow:
            descriptions = [self._EventDict['HOMEDESCRIPTION'], self._EventDict['VISITORDESCRIPTION'],
                        self._EventDict['NEUTRALDESCRIPTION']]
            for des in descriptions:
                if des:
                    if re.match(r"^MISS", des):
                        return 'missed'
            return 'made'

    @cached_property
    @limit_to_types(['ShotMade', 'ShotMiss', 'FreeThrow'])
    def Result(self):
        data = self._EventDict
        if str(data['EVENTMSGTYPE']) == '1': return 'made'
        if str(data['EVENTMSGTYPE']) == '2': return 'missed'
        descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                        data['NEUTRALDESCRIPTION']]
        for des in descriptions:
            if des:
                if re.match(r"^MISS", des):
                    return 'missed'
        return 'made'

    @cached_property
    @limit_to_types('JumpBall')
    def Home(self):
        return parse_player(1, self._EventDict)

    @cached_property
    @limit_to_types('JumpBall')
    def Away(self):
        return parse_player(2, self._EventDict)

    @cached_property
    @limit_to_types('JumpBall')
    def Possession(self):
        return parse_player(3, self._EventDict)

    @cached_property
    @limit_to_types('Turnover')
    def Steal(self):
        return parse_player(2, self._EventDict)

    @cached_property
    @limit_to_types('Substitution')
    def Left(self):
        return parse_player(1, self._EventDict)

    @cached_property
    @limit_to_types('Substitution')
    def Entered(self):
        return parse_player(2, self._EventDict)

    @staticmethod
    def _NumOutof(data, group_no):
        descriptions = [data['HOMEDESCRIPTION'], data['VISITORDESCRIPTION'],
                        data['NEUTRALDESCRIPTION']]
        for des in descriptions:
            if des:
                m = re.search(r'(\d) of (\d)', des)
                if m:
                    return int(m.group(group_no))
        return None

    @cached_property
    @limit_to_types('FreeThrow')
    def Num(self):
        return self._NumOutof(self._EventDict, 1)

    @cached_property
    @limit_to_types('FreeThrow')
    def OutOf(self):
        return self._NumOutof(self._EventDict, 2)


def update_game_players(events):
    """Update the players in each row of the playbyplays"""
    # TODO can refactor this
    game = events[0]._Game
    for i, ev in enumerate(events):
        if i == 0:
            ev._UpdatePlayers(game.HomeStarters | game.AwayStarters)
            continue
        prev_ev = events[i - 1]
        on_court_players = prev_ev.OnCourtPlayers.copy()
        _on_court_copy = on_court_players.copy()
        # If another period, then it should fetch players starting the period from the API
        if ev.Period > prev_ev.Period:
            start_range = ev.OverallElapsedTime.seconds * 10 + 5
            j = i
            to_update_floor_players = True
            while to_update_floor_players:  # Locate the range to look up for the players
                forward_ev = events[j]
                if forward_ev.EventType == EventType.Substitution:
                    end_range = forward_ev.OverallElapsedTime.seconds * 10
                    on_court_players = game.FindPlayersInRange(start_range, end_range)
                    while len(on_court_players) != 10:
                        end_range -= 5
                        if end_range <= start_range:
                            raise AssertionError(
                                'Could not locate on floor players %s, %s' % (start_range, end_range))
                        on_court_players = game.FindPlayersInRange(start_range, end_range)
                    to_update_floor_players = False
                else:
                    j += 1
                    if j == len(game._playbyplay['resultSets']['PlayByPlay']):
                        # if no sub at all after the increase in period, \
                        # then find the players on court of all remaining time.
                        end_range = forward_ev.OverallElapsedTime.seconds * 10
                        on_court_players = game.FindPlayersInRange(start_range, end_range)
                        assert len(on_court_players) == 10
                        to_update_floor_players = False
        if ev.EventType == EventType.Substitution:
            on_court_players.remove(ev.Left)
            on_court_players.add(ev.Entered)
            assert on_court_players != _on_court_copy
        ev._UpdatePlayers(on_court_players)
    return events


__all__ = ['Event']
