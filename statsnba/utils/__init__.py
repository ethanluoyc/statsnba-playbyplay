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
