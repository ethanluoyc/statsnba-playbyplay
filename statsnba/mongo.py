# This module wraps up our model definition and adds additional functionality for interacting with MongoDB
from mongoengine import *
from models.nba import NBAGame, NBAMatchup


# these are always only available within the context of a game
class PlayByPlay(EmbeddedDocument):
    home_player_ids = SortedListField(IntField())   # TODO why inconsistent with EmbeddedDocumentListField?
    away_player_ids = SortedListField(IntField())   # these needs to be updated by querying the API
    event = DictField()                             # information about the event(playbyplay)


class Matchup(EmbeddedDocument):
    matchup_num = IntField(required=True)
    start_play_id = IntField(required=True)
    end_play_id = IntField(required=True)
    elapsed_time = DateTimeField()
    stats = DictField()                             # various metrics for that matchup

    @property
    def _pbps(self):
        """ Return the segment of playbyplays for this matchup"""
        game_pbps =  self._instance.playbyplays
        return [p for p in game_pbps if (p.event['play_id'] >= self.start_play_id) and (p.event['play_id'] <= self.end_play_id)]

    @property
    def home_player_ids(self):
        return self._pbps[0].home_player_ids

    @property
    def away_player_ids(self):
        return self._pbps[0].away_player_ids

    # Below are metrics
    # TODO complete different metrics


class Game(Document):
    game_id = StringField(required=True, unique=True)
    _playbyplay = DictField()                            # fetched from stats.nba.com
    _boxscore = DictField()                              # fetched from stats.nba.com
    playbyplays = EmbeddedDocumentListField(PlayByPlay)  # parsed playbyplay
    matchups = EmbeddedDocumentListField(Matchup)        # parsed matchup

    @classmethod
    def create_game(cls, game_id):
        nbagame = NBAGame(game_id=game_id)
        game = Game(game_id=game_id, _playbyplay=nbagame._pbp, _boxscore=nbagame._boxscore)

        # Update the playbyplays
        pbps = []
        for p in nbagame.playbyplay:
            pbp = PlayByPlay()
            pbp.home_player_ids = [player.id for player in p.home_players]
            pbp.away_player_ids = [player.id for player in p.away_players]
            column_str = '| game_id | period | away_score | home_score | home_team | away_team | \
                            play_length | play_id | team | event_type | away | home | block | assist | \
                            entered | left | num | opponent | outof | player | points | possession \
                            | reason | result | steal | type | \
                            shot_distance | original_x | original_y | converted_x | converted_y | \
                            description | period_elapsed_time | period_remaining_time | \
                            overall_elapsed_time | overall_remaining_time |'

            # TODO refactor this into creating directly from PlayByPlay
            row = {col: getattr(p, col, None) for col in [c.strip() for c in column_str.split('|') if c.strip()]}
            # TODO refactor for better compliance with Mongo Data types
            for col in ['period_elapsed_time', 'period_remaining_time','overall_elapsed_time','overall_remaining_time']:
                row[col] = str(row[col])
            # TODO need home_score & away_score update
            pbp.event = row
            pbps.append(pbp)

        # Update the matchups
        matchups = NBAMatchup.create_matchups(nbagame.playbyplay)
        game.matchups = [Matchup(**m) for m in matchups]
        game.save()
        return game


if __name__ == '__main__':
    connect('statsnba')
    Game.drop_collection()
    Game.create_game("0020901030")
