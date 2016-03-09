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
    output_columns = luigi.Parameter(default='')

    @staticmethod
    def split_columns(column_str, sep='|'):
        if not column_str:
            column_str = '| h1 | h2 | h3 | h4 | h5 | a1 | a2 | a3 | a4 | a5 | game_id | period | away_score | home_score | remaining_time | elapsed | play_length | play_id | team | event_type | away | home | block | entered | left | num | opponent | outof | player | points | possession | reason | result | steal | type | shot_distance | original_x | original_y | converted_x | converted_y | description | period_elapsed_time | overall_elapsed_time'
        return [s for s in map(str.strip, column_str.split(sep)) if s]

    def run(self):
        from statsnba.models.nba import NBAGame
        game = NBAGame(self.game_id)
        pbps = []
        for pbp in game.playbyplay:
            pbps.append(pbp.to_dict())
        import pandas as pd
        game_df = pd.DataFrame(pbps)

        output_columns = ProcessPlayByPlay.split_columns(self.output_columns)
        game_df = game_df[output_columns]
        game_df.to_csv('data/processed_playbyplay/%s.csv' % self.game_id, index=False)

    def output(self):
        return luigi.LocalTarget('data/processed_playbyplay/%s.csv' % self.game_id)


class ProcessAllPlayByPlay(luigi.Task):
    pass
