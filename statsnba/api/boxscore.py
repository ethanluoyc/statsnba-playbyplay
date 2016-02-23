from statsnba.api.statsnba import StatsNBAAPI


class BoxscoreTraditional(StatsNBAAPI):

    resource = 'boxscoretraditionalv2'
    default_params = {
        'EndPeriod': '10',
        'EndRange': '14400',
        'GameID': '0021500818',
        'RangeType': '0',
        'StartPeriod': '1',
        'StartRange': '0'
    }
