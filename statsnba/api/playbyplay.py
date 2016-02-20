from statsnba.api.statsnba import StatsNBAAPI


class PlayByPlay(StatsNBAAPI):

    resource = 'playbyplayv2'  # version 2 of the API
    default_params = {
        'EndPeriod': '10',
        'EndRange': '55800',
        'GameID': '0021500391',
        'RangeType': '2',
        'Season': '2015-16',
        'SeasonType': 'Regular Season',
        'StartPeriod': '1',
        'StartRange': '0'
    }

    @staticmethod
    def _get_table_formula(data, table_no=0):
        header = data['resultSets'][table_no]['headers']
        rows = data['resultSets'][table_no]['rowSet']
        return header, rows

    def __init__(self, params, fetcher=None):
        super().__init__(params, fetcher)

        urls = []
        for p in self.params:
            urls.append(super(PlayByPlay, self)._encode_url(PlayByPlay.resource, p))

        self.fetcher.fetch(urls)
        self.data = self.fetcher.get()

    def __str__(self):
        return self.data.__str__()
