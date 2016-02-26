from .basespider import NBABaseSpider


class GamelogSpider(NBABaseSpider):
    resource = 'leaguegamelog'
    name = resource
    default_params = {
        "Direction": "DESC",
        "Sorter": "PTS",
        "Counter": 1000,
        "PlayerOrTeam": "T",
        "SeasonType": "Regular Season",
        "Season": None,
        "LeagueID": "00"
    }

    def __init__(self, seasons):
        super(GamelogSpider, self).__init__()

        def _parse_consecutive_seasons(seasons):
            start_season, end_season = seasons.split('-')
            print start_season, end_season
            return range(int(start_season), int(end_season)+1)

        seasons = _parse_consecutive_seasons(seasons)

        for season in seasons:
            s = self._parse_season(season)
            params = {'Season': s}
            params = self._update_params(params)
            self._validate_params(params)
            self.start_urls.append(self._encode_url(params))

    @staticmethod
    def _parse_season(year):
        """
            :param year string of year (e.g. 2012, 2013)
            :return season valid string of season used by the API.
                    (e.g. 2015-16, 2012-13)
        """
        next_yr = str(year+1)[-2:]
        return '{0}-{1}'.format(year, next_yr)
