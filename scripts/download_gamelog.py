from statsnba.api.games import LeagueGameLog
from statsnba.utils import make_season
from pymongo import MongoClient


mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client.test


params = {
        'EndPeriod': '10',
        'EndRange': '55800',
        'GameID': None,
        'RangeType': '2',
        'Season': '2015-16',
        'SeasonType': 'Regular Season',
        'StartPeriod': '1',
        'StartRange': '0'
    }


if __name__ == "__main__":
    params_list = []
    for year in range(2006, 2016):
        params['Season'] = make_season(year)
        params_list.append(params.copy())
    log = LeagueGameLog(params_list)
    db['gamelogs'].insert_many(log.data)
