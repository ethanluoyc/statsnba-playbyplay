import luigi
from statsnba.resources import *


class StatsNBAGamelogTask(luigi.ExternalTask, StatsNBAGamelog):
    season = luigi.Parameter()

    def run(self):
        result = self.fetch_resource()
        with self.output().open('w') as out_file:
            json.dump(result, out_file)

    def output(self):
        return luigi.LocalTarget('data/statsnba/gamelogs/gamelogs_%s.json' % self.season)


class GameIDs(luigi.Task):
    season = luigi.Parameter()

    def requires(self):
        return StatsNBAGamelogTask(season=self.season)

    def run(self):
        with self.input().open('r') as in_file:
            result_dict = json.load(in_file)
        with self.output().open('w') as out_file:
            for g in result_dict['resultSets']['LeagueGameLog']:
                print >>out_file, g['GAME_ID']

    def output(self):
        return luigi.LocalTarget('data/statsnba/game_ids_%s.csv' % self.season)


class ProcessPlayByPlay(luigi.ExternalTask):
    game_id = luigi.Parameter()

    def run(self):
        from statsnba.models.nba import NBAGame
        game = NBAGame(self.game_id)
        pbps = []
        for pbp in game.playbyplay:
            pbps.append(pbp.to_dict())
        import pandas as pd
        pd.DataFrame(pbps).to_csv('data/processed_playbyplay/%s.csv' % self.game_id)

    def output(self):
        return luigi.LocalTarget('data/processed_playbyplay/%s.csv' % self.game_id)


class AllPlayByPlay(luigi.Task):
    pass
