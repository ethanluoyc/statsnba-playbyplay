from statsnba.statsnba import StatsNBAAPI


class LeagueGameLog(StatsNBAAPI):

    resource = 'leaguegamelog'
    default_params = dict()

    @staticmethod
    def _get_table_formula(data, table_no=0):
        header = data['resultSets'][table_no]['headers']
        rows = data['resultSets'][table_no]['rowSet']
        return header, rows

    def __init__(self, params, fetcher=None):
        super().__init__(fetcher)
        if type(params) is not list:
            params = [params]
        self.params = params

        urls = []
        for p in params:
            urls.append(super(LeagueGameLog, self)._encode_url(LeagueGameLog.resource, p))

        self.fetcher.fetch(urls)
        self.data = self.fetcher.get()

        # import pandas as pd
        # columns, data = LeagueGameLog._get_table_formula(json_data)
        # self.df = pd.DataFrame(data, columns=columns)

    def to_json(self, **kargs):
        return self.df.to_json(**kargs)

    def to_df(self):
        return self.df

    def get_all_games(self):
        return self.df['GAME_ID']

    def __str__(self):
        return self.data.__str__()
