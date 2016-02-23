"""
This script converts the resultSets field (a list) into
common JSON format (a dict of key-value pairs)
"""

from statsnba.utils import convert_result
from pymongo import MongoClient


mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client.test

if __name__ == '__main__':
    for c in db.gamelogs.find(modifiers={"$snapshot": True}):
        resultSets = map(convert_result, c['resultSets'])
        c['resultSets'] = {}
        for name, data in resultSets:
            c['resultSets'][name] = data
        db.gamelogs.save(c)
