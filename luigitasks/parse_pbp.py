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


class StatsNBABoxscoreTask(luigi.ExternalTask, StatsNBABoxscore):
    game_id = luigi.Parameter()

    def run(self):
        pass

    def output(self):
        return luigi.LocalTarget('data/statsnba/boxscore/boxscore_%s.csv' % self.game_id)


class StatsNBAPlayByPlayTask(luigi.ExternalTask, StatsNBAPlayByPlay):
    game_id = luigi.Parameter()

    def run(self):
        pass

    def output(self):
        return luigi.LocalTarget('data/statsnba/pbp/playbyplay_%s.csv' % self.game_id)


class ProcessPlayByPlay(luigi.Task):
    game_id = luigi.Parameter()

    def requires(self):
        return {
                'boxscore': StatsNBABoxscoreTask(game_id=self.game_id),
                'pbp': StatsNBAPlayByPlayTask(game_id=self.game_id)
            }

    def run(self):
        boxscore = json.load(self.input()['boxscore'].open('r'))
        pbp = json.load(self.input()['pbp'].open('r'))

    def output(self):
        pass


if __name__ == '__main__':
    pass
