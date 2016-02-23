import urllib.parse


def encode_url(url, params):
    p = urllib.parse.urlencode(params)
    return url + '?' + p


def make_season(year):
    """
        :param year string of year (e.g. 2012, 2013)
        :return season valid string of season used by the API. (e.g. 2015-16, 2012-13)
    """
    next_yr = str(year+1)[-2:]
    return '{0}-{1}'.format(year, next_yr)


def make_table(doc):
    header = doc['resultSets'][0]['headers']
    rows = doc['resultSets'][0]['rowSet']
    import pandas as pd
    df = pd.DataFrame(rows, columns=header)
    for k, v in doc['parameters'].items():
        df[k] = v
    return df


def convert_result(result_dict):
    """
        :param result_dict the dict containing the headers, name and rowSet (see sample_data)
        :return (name, data) a tuple containing the name of the resultSet and data
    """
    result_name = result_dict['name']
    headers = result_dict['headers']
    data = result_dict['rowSet']
    import pandas as pd
    df = pd.DataFrame(data, columns=headers)
    return result_name, df.to_dict(orient='records')
