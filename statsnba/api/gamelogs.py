from statsnba.api.statsnba import StatsNBAAPI


class LeagueGameLog(StatsNBAAPI):

    resource = 'leaguegamelog'
    default_params = {
        "Direction": "DESC",
        "Sorter": "PTS",
        "Counter": 1000,
        "PlayerOrTeam": "T",
        "SeasonType": "Regular Season",
        "Season": None,
        "LeagueID": "00"
    }
