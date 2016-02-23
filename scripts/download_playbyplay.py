# coding: utf-8

import sys
sys.path.append('..')
from statsnba.api.playbyplay import PlayByPlay
from pymongo import MongoClient

import logging
logging.basicConfig(level=logging.INFO)

mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client.test


pipelines = [
                {'$project': { 'game_id': '$resultSets.LeagueGameLog'}},
                {'$unwind': '$game_id' },
                {'$group': {'_id': "$game_id.GAME_ID", 'count': { '$sum': 1} }}
            ]


game_ids = []
for c in db.gamelogs.aggregate(pipelines):
    game_ids.append(c['_id'])


params_list = []
for i in game_ids:
    param = {'GameID': i}
    params_list.append(param)

pbp = PlayByPlay(params_list)
db['playbyplay'].drop()
db['playbyplay'].insert_many(pbp.data)
