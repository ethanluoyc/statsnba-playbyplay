from statsnba.models import Player, Game


def test_player(sample_boxscore):
    stats_dict = sample_boxscore['resultSets']['PlayerStats'][0]
    p = Player(stats_dict)
    assert p.PlayerId == 2222
    assert p.PlayerName == "Gerald Wallace"
