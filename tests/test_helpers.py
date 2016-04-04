import pytest
from luigitasks.helpers import get_all_players, LineupTransformer
import pandas as pd
import itertools
import functools


def _make_cols(s):
    return list(itertools.chain(*[['home_player_{}_name'.format(i)] for i in range(1, 6)]))

home_player_name_cols = functools.partial(_make_cols, s='home_player_{}_name')()
home_player_id_cols = functools.partial(_make_cols, s='home_player_{}_id')()
away_player_name_cols = functools.partial(_make_cols, s='away_player_{}_name')()
away_player_id_cols = functools.partial(_make_cols, s='away_player_{}_id')()


def test_get_all_names():
    lineup_df = pd.DataFrame([
        dict(zip(home_player_name_cols, 'ABCDE')),
        dict(zip(home_player_name_cols, 'ABCEF')),
    ])

    players = get_all_players(lineup_df, player_cols=home_player_name_cols)
    assert len(players) == 6

    assert 'G' not in players
    assert 'F' in players


def test_lineup_transformer():
    players = list("ABCDEF")

    lineup_df = pd.DataFrame([
        dict(zip(['p1', 'p2', 'o1', 'o2'], ['A', 'B', 'C', 'D'])),
        dict(zip(['p1', 'p2', 'o1', 'o2'], ['A', 'E', 'C', 'F'])),
    ])

    X = LineupTransformer(players, pos_cols=['p1', 'p2'], neg_cols=['o1', 'o2']).fit_transform(lineup_df)
    assert X.shape[0] == len(lineup_df)
    assert X.sum().any() == 0
