# coding: utf-8

import sys
sys.path.append('..')
from statsnba.api.playbyplay import PlayByPlay
from pymongo import MongoClient

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('requests').setLevel(logging.ERROR)


mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client.test

pipelines = [
                {'$project': {'game_id': '$resultSets.LeagueGameLog'}},
                {'$unwind': '$game_id'},
                {'$group': {'_id': "$game_id.GAME_ID", 'count': {'$sum': 1}}}
            ]


def is_downloaded(collection, game_id):
    if collection.find_one({'parameters.GameID': str(game_id)}):
        return True
    return False

if __name__ == '__main__':
    # db['playbyplay'].drop()
    game_ids = []
    for c in db.gamelogs.aggregate(pipelines):
        game_ids.append(c['_id'])

    params_list = []
    for i in game_ids:
        if not is_downloaded(db['playbyplay'], i):
            param = {'GameID': i}
            params_list.append(param)

    print('Total there are {} records'.format(len(params_list)))
    # pbp = PlayByPlay(params_list, collection=db['playbyplay'])
