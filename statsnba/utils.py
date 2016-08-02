# -*- coding: utf-8 -*-
import urllib
import json


def encode_url(url, params):
    p = urllib.urlencode(params)
    return url + '?' + p


def make_season(year):
    """
        :param year string of year (e.g. 2012, 2013)
        :return season valid string of season used by the API. \
            (e.g. 2015-16, 2012-13)
    """
    next_yr = str(year+1)[-2:]
    return '{0}-{1}'.format(year, next_yr)


def convert_season_to_season_id(season):
    return '2' + season.split('-')[0]


def convert_resultset(result_dict):
    """
        :param result_dict the dict containing the headers, name and rowSet
               (see sample_data)
        :return (name, data) a tuple containing the name of the
               resultSet and data
    """
    result_name = result_dict['name']
    headers = result_dict['headers']
    data = result_dict['rowSet']
    import pandas as pd
    df = pd.DataFrame(data, columns=headers)
    # use this to avoid Mongo conversion error
    return result_name, json.loads(df.to_json(orient='records'))
