import pytest
import pandas as pd


@pytest.fixture(params=['Home',
                        'Away'])
def computed_actual_team_stats(request, game):
    matchups = game.Matchups
    boxscores = [matchup.Boxscore for matchup in matchups]
    if request.param == 'Home':
        homeSplitBox = [b.HomeTeamStats for b in boxscores]
        return pd.DataFrame(homeSplitBox).sum().to_dict(), game._HomeBoxscore
    else:
        awaySplitBox = [b.AwayTeamStats for b in boxscores]
        return pd.DataFrame(awaySplitBox).sum().to_dict(), game._AwayBoxscore


@pytest.mark.parametrize('field', [
        "TO",
        "REB",
        "FG3A",
        "AST",
        "FG3M",
        "OREB",
        "FGM",
        "PF",
        "PTS",
        "FGA",
        "PLUS_MINUS",
        "STL",
        "FTA",
        "BLK",
        "DREB",
        "FTM"
        ])
def test_matchup_stats_equality(computed_actual_team_stats, field):
    """This test helps to verify that matchups' stats of the game aggregate to the game's stats"""
    computed = computed_actual_team_stats[0]
    actual = computed_actual_team_stats[1]
    assert computed[field] == actual[field]


@pytest.mark.parametrize('field', [
    "FT_PCT",
    "FG_PCT",
    "FG3_PCT",
])
def test_matchup_stats_percentage(computed_actual_team_stats, field):
    computed = computed_actual_team_stats[0]
    actual = computed_actual_team_stats[1]
    import re
    num = computed[re.sub('_PCT', 'M', field)]
    denom = computed[re.sub('_PCT', 'A', field)]
    assert abs((num / float(denom)) - actual[field]) < 0.05

