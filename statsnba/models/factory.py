from .mongo import MongoGame, MongoPlayer, MongoEvent


class Backend(object):
    team = NotImplementedError
    event = NotImplementedError
    player = NotImplementedError
    game = NotImplementedError


class Event(object):
    def __init__(self, backend='mongo', **kargs):
        if backend == 'mongo':
            self._backend = MongoEvent(**kargs)  # can further refactor

    def __eq__(self, other_player):
        return self._backend.__eq__(other_player)

    def __getattr__(self, item):
        return getattr(self._backend, item)


class Player(object):
    def __init__(self, backend='mongo', **kargs):
        if backend == 'mongo':
            self._backend = MongoPlayer(**kargs)

    def __getattr__(self, item):
        return getattr(self._backend, item)

    def __hash__(self):
        return self._backend.__hash__()

    def __eq__(self, other):
        return self._backend.__eq__(other_player)
        # return self.name == other.name and self.team_abbr == other.team_abbr

    def __repr__(self):
        return '<{}, {}>'.format(self.name, self.team_abbr)


class Game(object):
    def __init__(self, backend='mongo', **kargs):
        if backend == 'mongo':
            self._backend = MongoGame(game_id=kargs.pop('game_id'))

    def __getattr__(self, item):
        return getattr(self._backend, item)

    @property
    def lineups(self):
        lineups = []
        group = []
        for i, evt in enumerate(self.playbyplay[:-1]):
            if evt.players == self.playbyplay[i+1].players:
                group.append(evt)
            elif evt.players != self.playbyplay[i-1].players:
                group.append(evt)
            else:
                lineups.append(group)
                group = []
        return lineups

    def possessions(self):
        pass


class MongoStats(object):
    pass
