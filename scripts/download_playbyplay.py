from statsnba.api.playbyplay import PlayByPlay
from statsnba.utils import make_season, make_table
from pymongo import MongoClient

import logging
logging.getLogger('requests').setLevel(logging.WARN)  # comment out this if you need to see the logs
logging.basicConfig(level=logging.INFO)


mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client.test


params = {
        'EndPeriod': '10',
        'EndRange': '55800',
        'GameID': '0021500391',
        'RangeType': '2',
        'Season': '2015-16',
        'SeasonType': 'Regular Season',
        'StartPeriod': '1',
        'StartRange': '0'
    }


def find_games(col, query):
    """Finds valid records with queries from MongoDB
    :param col collection in the db
    :param query the query for finding in the document
    """
    cursor = col.find(query)
    dfs = list(map(make_table, cursor))
    return dfs

if __name__ == "__main__":
    query = {'parameters.Season': {"$in": ["2015-16", "2013-14"]}}
    dfs = find_games(db.gamelogs, query)
    import json
    params_list = []
    for df in dfs:
        json_data = json.loads(df.to_json(orient='records'))
        for r in json_data:
            params.update({'GameID': r['GAME_ID'],
                           'Season': r['Season']})
            params_list.append(params.copy())
    pbp = PlayByPlay(params=params_list[0:10])

    db.playbyplay.drop()
    db.playbyplay.insert_many(pbp.data)
