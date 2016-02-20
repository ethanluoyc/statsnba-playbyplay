from statsnba.api.statsnba import StatsNBAAPI


class LeagueGameLog(StatsNBAAPI):

    resource = 'leaguegamelog'
    default_params = dict()

    @staticmethod
    def _get_table_formula(data, table_no=0):
        header = data['resultSets'][table_no]['headers']
        rows = data['resultSets'][table_no]['rowSet']
        return header, rows

    def __init__(self, params, fetcher=None):
        super().__init__(params, fetcher)

        urls = []
        for p in self.params:
            urls.append(super(LeagueGameLog, self)._encode_url(LeagueGameLog.resource, p))

        self.fetcher.fetch(urls)
        self.data = self.fetcher.get()

    def __str__(self):
        return self.data.__str__()
