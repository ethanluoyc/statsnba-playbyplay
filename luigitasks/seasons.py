import luigi
from playbyplays import SeasonPlayByPlay
from matchups import SeasonMatchups, AggregateSeasonMatchups


class ManySeasonsTask(luigi.WrapperTask):
    seasons = luigi.parameter.Parameter(description="""
                                            multiple seasons in the format {START_SEASON}-{END_SEASON (inclusive)}
                                            e.g. '2009-2014' refers to seasons from 2009-2010 to 2014-2015
                                        """)
    season_task = luigi.TaskParameter(description="""
                                            The task to run for each season
                                        """)

    def requires(self):
        start_season, end_season = self.seasons.split('-')
        for season in range(int(start_season), int(end_season)+1):
            yield self.season_task(season=season)
