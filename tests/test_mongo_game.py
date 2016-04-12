from statsnba.models.mongo import Game, Player, Team, Event, Matchup
import pytest
from datetime import timedelta

# Sample game from http://stats.nba.com/game/#!/0020901030/
# MIA vs. CHA
@pytest.fixture(scope='module')
def sample_game(mongodb):
    game = Game.create_game('0020901030')
    return game


home_team = Team('MIA', 1610612748)
away_team = Team('CHA', 1610612766)
@pytest.mark.parametrize("info,value", [
    ('game_id', '0020901030'),
    ('home_team', home_team),
    ('away_team', away_team),
    ('game_length', timedelta(minutes=48))
])
def test_game_info(sample_game, info, value):
    assert getattr(sample_game, info) == value


def test_players_groups(sample_game):
    assert len(sample_game.players) == 12 + 12
    # Home team is Miami Heat (MIA)
    ## Sanity check on no. of players
    assert len(sample_game.home_players) == 12
    assert len(sample_game.home_starters) == 5
    assert len(sample_game.away_bench) == 12 - 5

    Quentin_Richardson = Player(name='Quentin Richardson', id=2047, team=home_team)
    assert Quentin_Richardson in sample_game.home_starters
    assert Quentin_Richardson not in sample_game.home_bench

    James_Jones = Player(name='James Jones', id=2592, team=home_team)
    assert James_Jones not in sample_game.home_starters
    assert James_Jones in sample_game.home_bench

    # Away team is Charlotte Bobcats (CHA)
    ## Sanity check on no. of players
    assert len(sample_game.away_players) == 12
    assert len(sample_game.away_starters) == 5
    assert len(sample_game.away_bench) == 12 - 5

    Gerald_Wallace = Player(name='Gerald Wallace', id=2222, team=away_team)
    assert Gerald_Wallace in sample_game.away_starters
    assert Gerald_Wallace not in sample_game.away_bench

    Tyrus_Thomas = Player('Tyrus Thomas', 200748, away_team)
    assert Tyrus_Thomas not in sample_game.away_starters
    assert Tyrus_Thomas in sample_game.away_bench


def test_find_player(sample_game):
    Tyrus_Thomas = Player('Tyrus Thomas', 200748, away_team)
    sample_game._find_player('Tyrus Thomas') == Tyrus_Thomas


# Below tests for the parsing of playbyplay data from the raw format fetched
def test_process_playbyplays(sample_game, use_requests_cache):
    assert len(sample_game.playbyplay) == 450 # Sanity Check


def test_playbyplay_update_players(sample_game, use_requests_cache):
    playbyplay = sample_game.playbyplay
    # *NOTE*: the index here is not the play_id. There are gaps in play_id in between
    assert playbyplay[0].players == sample_game.home_starters | sample_game.away_starters
    assert playbyplay[1].players == playbyplay[2].players    # Carry forward the players from previous event
    assert playbyplay[43].players == playbyplay[42].players  # It should have the same players cuz no sub here
    assert playbyplay[43].players == playbyplay[44].players  # It should have the same players cuz no sub here
    assert playbyplay[45].players != playbyplay[44].players  # After a sub, it should have different players


@pytest.mark.parametrize("matchup_no,start_id,end_id", [
    (0, 0, 51),                      # 2 consecutive subs
    (1, 52, 80),
    (2, 81, 88),                     # 1 substitution in the end
    (3, 89, 106),                    # Change in period
    (4, 108, 115),                     # Change in period
    (5, 117, 120),                     # Change in period
    (6, 121, 151)                    # 3 consecutive subs at the bottom
])
def test_parse_matchups(sample_game, use_requests_cache, matchup_no, start_id, end_id):
    # Checks for the correct split of the playbyplay into matchups, check annotations in sample data for verification.
    from statsnba.models.mongo import Matchup
    matchups = list(Matchup.create_matchups(sample_game.playbyplay))
    assert matchups[matchup_no][0].play_id == start_id
    assert matchups[matchup_no][-1].play_id == end_id


@pytest.mark.parametrize("team,boxscore_expected", [
    ('home', dict(FGM=28,FGA=78, FG3M=7, FG3A=28, FTM=14, FTA=20, OREB=13, DREB=37, REB=50, AST=19, TOV=10, STL=6, BLK=13, PF=27)),
    # TODO error with home PF parsing, maybe an error in the API?
    ('away', dict(FGM=21,FGA=72, FG3M=2, FG3A=13, FTM=27, FTA=34, OREB=8,  DREB=35, REB=43, AST=8,  TOV=15, STL=7, BLK=5,  PF=21)),
], ids=['MIA', 'CHA'])
def test_matchup_boxscores(sample_game, team, boxscore_expected):
    from statsnba.models.mongo import Matchup
    import pandas as pd
    matchups = list(Matchup.create_matchups(sample_game.playbyplay))
    stats = []
    for i, m in enumerate(iter(matchups)):
        group = pd.DataFrame([e.to_dict() for e in m])
        stats.append(Matchup.compute_boxscore(group, team))
    stats = pd.DataFrame(stats).sum().to_dict()
    for k in boxscore_expected.keys():
        assert stats[k] == boxscore_expected[k], "Boxscore item mismatch, %s" % k
