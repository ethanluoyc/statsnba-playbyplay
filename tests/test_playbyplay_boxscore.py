import pytest
import pandas as pd

from luigitasks.playbyplays import ProcessPlayByPlay
from statsnba.models.nba import NBAGame


game_ids = ['0021400120',
            '0020900793',
            '0020900054'
            ]


@pytest.fixture(params=game_ids, ids=game_ids)
def game(request):
    game_id = request.param
    game = NBAGame(game_id)
    print game
    return game


def test_parse_playbyplays(game):
    # It should parse all the play-by-plays without error
    assert game.playbyplay


def test_verify_playbyplay_boxscore(game):
    # verify the boxscores aggregated from matchups against that from official boxscores
    pbps = []
    output_columns = ProcessPlayByPlay.split_columns('')
    for pbp in game.playbyplay:
        row = {col: getattr(pbp, col) for col in output_columns}
        pbps.append(row)  # TODO refactor pbp to be iterable as a data source by default
    pbp = pd.DataFrame(pbps)

    def check_team_boxscores(stats, team):

        home_msk = pbp['team'] == game.home_team
        away_msk = pbp['team'] == game.away_team

        FGM_msk = pbp['event_type'] == 'shot made'
        FGA_msk = (pbp['event_type'] == 'shot made') | (pbp['event_type'] == 'shot missed')

        FG3M_msk = (pbp['event_type'] == 'shot made') & (pbp['points'] == 3)
        FG3A_msk = ((pbp['event_type'] == 'shot made') | (pbp['event_type'] == 'shot missed')) & (pbp['type'].str.contains('3 points'))

        FTM_msk = (pbp['event_type'] == 'free throw') & (pbp['result'] == 'made')
        FTA_msk = (pbp['event_type'] == 'free throw')

        OREB_msk = (pbp['event_type'] == 'offensive rebound')
        DREB_msk = (pbp['event_type'] == 'defensive rebound')
        REB_msk = (pbp['event_type'] == 'offensive rebound') | (pbp['event_type'] == 'defensive rebound')

        AST_msk = pbp['assist'].notnull()
        TOV_msk = (pbp['event_type'] == 'turnover')
        STL_msk = pbp['steal'].notnull()
        BLK_msk = pbp['block'].notnull()
        PF_msk = (pbp['event_type'] == 'foul')

        def closure():
            assert team in ['home', 'away']
            if team == 'home':
                team_msk = home_msk
            else:
                team_msk = away_msk
            assert len(pbp[team_msk & locals()[stats+'_msk']]) == getattr(game, team+'_boxscore')[stats]

        return closure

    for team in ['home', 'away']:
        for stats in 'FGM,FGA,FG3M,FG3A,FTM,FTA,OREB,DREB,REB,AST,TOV,STL,BLK,PF'.split(','):
            check_team_boxscores(stats, team)
