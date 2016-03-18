import luigi
from statsnba.resources import *
import pandas as pd
from statsnba.utils import make_season


def get_season_game_ids(season):
    gamelog = StatsNBAGamelog.fetch_resource({'Season': season})
    game_ids = []
    for g in gamelog['resultSets']['LeagueGameLog']:
        game_ids.append(g['GAME_ID'])
    return game_ids


class StatsNBAPlayerStatsTask(luigi.ExternalTask, StatsNBALeaguePlayerStats):
    season = luigi.Parameter()

    def run(self):
        season = make_season(int(self.season))
        result = self.fetch_resource({'Season': season,
                                      'PerMode': 'Totals'})
        with self.output().open('w') as out_file:
            pd.DataFrame(result['resultSets']['LeagueDashPlayerStats']).to_csv(out_file)

    def output(self):
        return luigi.LocalTarget('data/statsnba/playerstats/playerstats_%s.csv' % self.season)


class ManySeasonsPlayerStats(luigi.WrapperTask):
    seasons = luigi.parameter.Parameter()

    def requires(self):
        start_season, end_season = self.seasons.split('-')
        for season in range(int(start_season), int(end_season)+1):
            yield StatsNBAPlayerStatsTask(season=season)


class StatsNBAGamelogTask(luigi.ExternalTask, StatsNBAGamelog):
    season = luigi.Parameter()

    def run(self):
        result = self.fetch_resource({'Season': self.season})
        with self.output().open('w') as out_file:
            json.dump(result, out_file)

    def output(self):
        return luigi.LocalTarget('data/statsnba/gamelogs/gamelogs%s.json' % self.season)


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


class ProcessPlayByPlay(luigi.Task):
    game_id = luigi.Parameter()
    output_columns = luigi.Parameter(default='')
    output_file_format = 'playbyplays_{game_id}.csv'

    @staticmethod
    def split_columns(column_str, sep='|'):
        import itertools
        if not column_str:
            columns = []
            columns.extend(list(itertools.chain(*[['home_player{}_id'.format(i), 'home_player{}_name'.format(i)] for i in range(1, 6)])))
            columns.extend(list(itertools.chain(*[['away_player{}_id'.format(i), 'away_player{}_name'.format(i)] for i in range(1, 6)])))
            column_str = '| game_id | period | away_score | home_score | home_team | away_team | \
                            play_length | play_id | team | event_type | away | home | block | assist | \
                            entered | left | num | opponent | outof | player | points | possession \
                            | reason | result | steal | type | \
                            shot_distance | original_x | original_y | converted_x | converted_y | \
                            description | period_elapsed_time | period_remaining_time | \
                            overall_elapsed_time | overall_remaining_time |'

            columns.extend([s for s in map(str.strip, column_str.split(sep)) if s])
            return columns
        return [s for s in map(str.strip, column_str.split(sep)) if s]

    def run(self):
        from statsnba.models.nba import NBAGame
        game = NBAGame(self.game_id)
        pbps = []
        output_columns = ProcessPlayByPlay.split_columns(self.output_columns)
        for pbp in game.playbyplay:
            row = {col: getattr(pbp, col) for col in output_columns}
            pbps.append(row)
        import pandas as pd
        game_df = pd.DataFrame(pbps)[output_columns]
        game_df[['away_score', 'home_score']] = game_df[['away_score', 'home_score']].fillna(method='ffill')
        game_df[['away_score', 'home_score']] = game_df[['away_score', 'home_score']].fillna(0)
        # Clean the data by filling na
        game_df.to_csv(('data/processed_playbyplay/' + self.output_file_format).format(game_id=self.game_id), index=False)

    def output(self):
        return luigi.LocalTarget(('data/processed_playbyplay/' + self.output_file_format).format(game_id=self.game_id))


class SeasonPlayByPlay(luigi.WrapperTask):
    season = luigi.parameter.Parameter()

    def requires(self):
        from statsnba.utils import make_season
        season = make_season(int(self.season))
        game_ids = get_season_game_ids(season)

        for g in game_ids:
            yield ProcessPlayByPlay(game_id=g.strip())
