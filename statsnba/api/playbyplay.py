from statsnba.api.statsnba import StatsNBAAPI


class PlayByPlay(StatsNBAAPI):

    resource = 'playbyplayv2'  # version 2 of the API
    default_params = {
        'EndPeriod': '10',
        'GameID': None,
        'StartPeriod': '1'
    }
