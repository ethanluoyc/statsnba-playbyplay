import pytest
from unittest import TestCase
from os import path
from statsnba.api.games import LeagueGameLog

SAMPLEDATA_DIR = path.join(path.dirname(__file__), '../sample_data/')

test_game_log = {
    'resultSets': [
        {"headers": ["SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME", "GAME_ID", "GAME_DATE", "MATCHUP", "WL", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PLUS_MINUS", "VIDEO_AVAILABLE"],
         "rowSet": [["22015", 1610612765, "DET", "Detroit Pistons", "0021500391", "2015-12-18", "DET @ CHI", "W", 340, 56, 124, 0.452, 8, 29, 0.276, 27, 46, 0.587, 19, 45, 64, 28, 7, 4, 11, 35, 147, 3, 1],
                    ["22015", 1610612741, "CHI", "Chicago Bulls", "0021500391", "2015-12-18", "CHI vs. DET", "L", 340, 50, 120, 0.417, 5, 22, 0.227, 39, 44, 0.886, 20, 42, 62, 21, 5, 9, 17, 35, 144, -3, 1]]
        }
    ]
}

class TestClass:

    def setUp(self):
        self.league_gamelog = LeagueGameLog()

    def test_get_all_games(self):
        pass
