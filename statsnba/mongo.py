# This module wraps up our model definition and adds additional functionality for interacting with MongoDB
from mongoengine import *
from models.nba import NBAGame


# these are always only available within the context of a game
class PlayByPlay(EmbeddedDocument):
    home_player_ids = SortedListField(IntField)
    away_player_ids = SortedListField(IntField) # these needs to be updated by quering the API
    event = DictField()                         # information about the event(playbyplay)


class Matchup(EmbeddedDocument):
    matchup_no = IntField(required=True)
    start_play_id = IntField(required=True)
    end_play_id = IntField(required=True)
    elapsed_time = DateTimeField()
    stats = DictField()                         # various metrics for that matchupp


class Game(Document):
    game_id = StringField(required=True, unique=True)
    _playbyplay = DictField()                            ## fetched from stats.nba.com
    _boxscore = DictField()                              ## fetched from stats.nba.com
    playbyplays = EmbeddedDocumentListField(PlayByPlay)  # parsed playbyplay
    matchups = EmbeddedDocumentListField(Matchup)        # parsed matchup

    @classmethod
    def create_game(cls, game_id):
        nbagame = NBAGame(game_id=game_id)
        game = Game(game_id=game_id, _playbyplay=nbagame._pbp, _boxscore=nbagame._boxscore)
        # TODO update the playbyplay and matchups here
        game.save()
        return game
