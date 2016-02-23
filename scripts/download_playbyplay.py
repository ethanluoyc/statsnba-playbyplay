from statsnba.api.boxscore import BoxscoreTraditional
from statsnba.api.playbyplay import PlayByPlay
from statsnba.utils import make_season, make_table
from pymongo import MongoClient

import logging
logging.getLogger('requests').setLevel(logging.WARN)  # comment out this if you need to see the logs
logging.basicConfig(level=logging.INFO)


mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client.test


playbyplay_params = {
        'EndPeriod': '10',
        'GameID': '0021500391',
        'StartPeriod': '1'
    }


boxscore_params = {
        'EndPeriod': '10',
        'EndRange': '14400',
        'GameID': '0021500818',
        'RangeType': '0',
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
    boxscore_params = []
    for df in dfs:
        json_data = json.loads(df.to_json(orient='records'))
        for r in json_data:
            playbyplay_params.update({'GameID': r['GAME_ID'],
                           'Season': r['Season']})
            params_list.append(playbyplay_params.copy())

        for r in json_data:
            boxscore_params.update({'GameID': r['GAME_ID'],
                                    'Season': r['Season']})
            boxscore_params.append(boxscore_params.copy())

    pbp = PlayByPlay(params=params_list[0:10])
    db.playbyplay.drop()
    db.playbyplay.insert_many(pbp.data)

    box = BoxscoreTraditional(params=params_list[0:10])
    db.boxscore.drop()
    db.boxscore.insert_many(box.data)
