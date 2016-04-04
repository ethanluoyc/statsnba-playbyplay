from sklearn.base import TransformerMixin
import numpy as np


def get_all_players(matchup_df, player_cols):
    """Helper function to get all the players in a line-up DataFrame"""
    return np.unique(matchup_df[player_cols])


class LineupTransformer(TransformerMixin):
    def __init__(self, players=None, pos_cols=None, neg_cols=None):
        self._players = players
        self._player_map = dict()
        for i, p in enumerate(self._players):
            self._player_map[str(p)] = i
        self.pos_cols = pos_cols
        self.neg_cols = neg_cols

    def fit(self, X, y=None, **fit_params):
        """
        :param X the line-up DataFrame
        """
        return self

    def transform(self, X):
        if not self._players:
            raise Exception('players not specified')

        transformed_X = np.zeros((len(X), len(self._players)))
        for i, row in X.iterrows():
            for col in self.pos_cols:
                player_idx = self._player_map[row[col]]
                transformed_X[i, player_idx] = 1
            for col in self.neg_cols:
                player_idx = self._player_map[row[col]]
                transformed_X[i, player_idx] = -1
        return transformed_X
