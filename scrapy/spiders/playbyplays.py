from .basespider import NBABaseSpider


class PlayByPlaySpider(NBABaseSpider):
    resource = 'playbyplay'
    default_params = {
        'EndPeriod': '10',
        'GameID': None,
        'StartPeriod': '1'
    }


