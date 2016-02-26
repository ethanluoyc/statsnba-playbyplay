from .basespider import NBABaseSpider


class BoxscoreSpider(NBABaseSpider):
    resource = 'boxscoretraditionalv2'
    name = 'boxscoretraditional'
    default_params = {
        'EndPeriod': '10',
        'EndRange': '14400',
        'GameID': None,
        'RangeType': '0',
        'StartPeriod': '1',
        'StartRange': '0'
    }

    def __init__(self, gameids_file):
        super(BoxscoreSpider, self).__init__()
        self.game_ids = self._read_game_ids(gameids_file)

        for id in self.game_ids:
            params = {'GameID': id}
            params = self._update_params(params)
            self._validate_params(params)
            self.start_urls.append(self._encode_url(params))

    @staticmethod
    def _read_game_ids(gameids_file):
        gameids = []
        import os
        with open(os.path.join(os.getcwd(), gameids_file), 'r') as f:
            for line in f.readlines():
                gameids.append(line.rstrip('\n'))
            return gameids
