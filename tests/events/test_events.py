from statsnba.models.events import parse_player, EventType


def test_parse_player(sample_playbyplay):
    sample_event_dict = sample_playbyplay['resultSets']['PlayByPlay'][1]
    p = parse_player(1, sample_event_dict)
    assert p.PlayerName == 'Joel Anthony'
    assert p.Team.TeamAbbreviation == 'MIA'


# Below tests the actual parsing of the events
def test_parse_event(sample_game_id, game):
    assert game.game_id == sample_game_id


def test_jump_shot(game):
    event = game.PlayByPlay[2]
    assert event.Period == 1


def test_limit_types(game):
    event = game.PlayByPlay[2]
    assert event.Home is None
    event = game.PlayByPlay[1]
    assert event.Home is not None


def test_jumpball(game):
    event = game.PlayByPlay[1]
    assert event.Away.PlayerName is not None


def test_substitution(game):
    event1 = game.PlayByPlay[45]
    assert event1.Entered.PlayerName == 'Tyson Chandler'
    assert event1.Left.PlayerName == 'Theo Ratliff'
    assert event1.EventType == EventType.Substitution

    event2 = game.PlayByPlay[46]
