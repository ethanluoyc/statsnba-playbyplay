import luigi
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017')
db = client.statsnba

pipelines = [{'$project': {'game_id': '$resultSets.LeagueGameLog'}},
             {'$unwind': '$game_id'},
             {'$group': {'_id': "$game_id.GAME_ID", 'count': {'$sum': 1}}}]


class FindGames(luigi.ExternalTask):
    def output(self):
        return luigi.LocalTarget("data/game_ids.txt")

    def run(self):
        with self.output().open('w') as out_file:
            for c in db.leaguegamelog.aggregate(pipelines):
                out_file.write(c['_id'] + '\n')
