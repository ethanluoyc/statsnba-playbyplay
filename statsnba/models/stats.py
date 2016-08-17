from statsnba.models.events import EventType
from cached_property import cached_property


class BoxscoreStats:
    _BoxscoreFields = ['FGM', 'FGA', 'FG_PCT',
                       'FG3M', 'FG3A', 'FG3_PCT',
                       'FTM', 'FTA', 'FT_PCT',
                       'REB', 'OREB', 'DREB',
                       'AST', 'BLK', 'TO', 'PF', 'STL',
                       'ElapsedTime', 'Possessions', 'PTS'
                       ]

    def __init__(self, event_lst):
        self._event_lst = event_lst

    @property
    def HomeTeamEvents(self):
        return [event for event in self._event_lst if event.Team and event.Team == event.HomeTeam]

    @property
    def AwayTeamEvents(self):
        return [event for event in self._event_lst if event.Team and event.Team == event.AwayTeam]

    @property
    def HomeTeamStats(self):
        team_event_lst = self.HomeTeamEvents
        stats_dict = {}
        for field in self._BoxscoreFields:
            stats_dict[field] = getattr(self, '_'+field)(team_event_lst)
        stats_dict['PLUS_MINUS'] = stats_dict['PTS'] - BoxscoreStats._PTS(self.AwayTeamEvents)
        stats_dict['STL'] = BoxscoreStats._STL(self.AwayTeamEvents)
        stats_dict['BLK'] = BoxscoreStats._BLK(self.AwayTeamEvents)
        return stats_dict

    @property
    def AwayTeamStats(self):
        team_event_lst = self.AwayTeamEvents
        stats_dict = {}
        for field in self._BoxscoreFields:
            stats_dict[field] = getattr(self, '_'+field)(team_event_lst)
        stats_dict['PLUS_MINUS'] = stats_dict['PTS'] - BoxscoreStats._PTS(self.HomeTeamEvents)
        stats_dict['STL'] = BoxscoreStats._STL(self.HomeTeamEvents)
        stats_dict['BLK'] = BoxscoreStats._BLK(self.HomeTeamEvents)
        return stats_dict

    # Functions to compute the boxscores

    @staticmethod
    def _PTS(team_event_lst):
        return sum([event.Points for event in team_event_lst if event.Points])

    @staticmethod
    def _FGM(team_event_lst):
        """Field Goal Made"""
        return sum([1 for event in team_event_lst if (event.EventType is EventType.ShotMade)])

    @staticmethod
    def _FGA(team_event_lst):
        """Field Goal Attempted"""
        return sum([1 for event in team_event_lst if (event.EventType in [EventType.ShotMade, EventType.ShotMiss])])

    @staticmethod
    def _FG_PCT(team_event_lst):
        """Field Goal Percentage"""
        FGM = BoxscoreStats._FGM(team_event_lst)
        FGA = BoxscoreStats._FGA(team_event_lst)
        try:
            return FGM / FGA
        except ZeroDivisionError:
            return 0

    @staticmethod
    def _FG3M(team_event_lst):
        """3 Pointers Made"""
        return sum([1 for event in team_event_lst if (event.EventType is EventType.ShotMade and
                                                      event.Type == '3 points')])

    @staticmethod
    def _FG3A(team_event_lst):
        """3 Pointers Attempted"""
        return sum([1 for event in team_event_lst if (event.EventType in [EventType.ShotMade, EventType.ShotMiss] and
                                                      event.Type == '3 points')])

    @staticmethod
    def _FG3_PCT(team_event_lst):
        """3 Pointers Percentage"""
        FG3M = BoxscoreStats._FG3M(team_event_lst)
        FG3A = BoxscoreStats._FG3A(team_event_lst)
        try:
            return FG3M / FG3A
        except ZeroDivisionError:
            return 0

    @staticmethod
    def _FTM(team_event_lst):
        """Free throws made"""
        return sum([1 for event in team_event_lst if (event.EventType is EventType.FreeThrow and
                                                      event.Result == 'made')])

    @staticmethod
    def _FTA(team_event_lst):
        """Free throws attempted"""
        return sum([1 for event in team_event_lst if (event.EventType is EventType.FreeThrow)])

    @staticmethod
    def _FT_GROUPS(team_event_lst):
        return sum([1 for event in team_event_lst if (event.EventType is EventType.FreeThrow and
                                                      event.Num == 1)])

    @staticmethod
    def _FT_PCT(team_event_lst):
        """Free throws percentage"""
        FTM = BoxscoreStats._FG3M(team_event_lst)
        FTA = BoxscoreStats._FG3A(team_event_lst)
        try:
            return FTM / FTA
        except ZeroDivisionError:
            return 0

    @staticmethod
    def _REB(team_event_lst):
        """Total Rebounds"""
        return sum([1 for event in team_event_lst if event.EventType is EventType.Rebound and event.Player])

    @staticmethod
    def _OREB(team_event_lst):
        """Offensive Rebounds"""
        return sum([1 for event in team_event_lst if (event.EventType is EventType.Rebound and event.Type == 'offensive'
                                                      and event.Player)])

    @staticmethod
    def _DREB(team_event_lst):
        """Defensive Rebounds"""
        return sum([1 for event in team_event_lst if (event.EventType is EventType.Rebound and event.Type == 'defensive'
                                                      and event.Player)])

    @staticmethod
    def _AST(team_event_lst):
        """Assists"""
        return sum([1 for event in team_event_lst if event.Assist])

    @staticmethod
    def _BLK(team_event_lst):
        """Blocks"""
        return sum([1 for event in team_event_lst if event.Block])

    @staticmethod
    def _STL(team_event_lst):
        """Steals"""
        return sum([1 for event in team_event_lst if event.Steal])

    @staticmethod
    def _PF(team_event_lst):
        """Personal Foul"""
        # Notice that a T.Foul is not recorded in PF
        return sum([1 for event in team_event_lst if event.EventType in [EventType.Foul, EventType.Violation]
                    and event._EventDict['PLAYER2_NAME']])

    @staticmethod
    def _TO(team_event_lst):
        return sum([1 for event in team_event_lst if event.EventType is EventType.Turnover])

    @staticmethod
    def _ElapsedTime(team_event_lst):
        if team_event_lst:
            return team_event_lst[-1].OverallElapsedTime - team_event_lst[0].OverallElapsedTime
        return 0

    @staticmethod
    def _Possessions(team_event_lst):
        """Number of Possessions"""
        FGA = BoxscoreStats._FGA(team_event_lst)
        OREB = BoxscoreStats._OREB(team_event_lst)
        TO = BoxscoreStats._TO(team_event_lst)
        FT_GROUPS = BoxscoreStats._FT_GROUPS((team_event_lst))
        return FGA - OREB + TO + FT_GROUPS
