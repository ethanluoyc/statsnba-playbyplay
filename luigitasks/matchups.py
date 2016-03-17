import luigi
import pandas as pd
from playbyplays import ProcessPlayByPlay, get_season_game_ids


class PbPToMatchups(luigi.Task):
    game_id = luigi.Parameter()
    output_file_format = 'matchups_{game_id}.csv'

    def requires(self):
        return ProcessPlayByPlay(game_id=self.game_id)

    def run(self):
        with self.input().open() as in_file:
            game_pbp = pd.read_csv(in_file,
                                   engine='c',
                                   dtype={'game_id': str},
                                   converters={'period_elapsed_time': pd.to_timedelta,
                                               'overall_elapsed_time': pd.to_timedelta,
                                               'period_remaining_time': pd.to_timedelta,
                                               'overall_remaining_time': pd.to_timedelta})

        # fill up the score columns for better tabulation
        game_pbp[['away_score', 'home_score']] = game_pbp[['away_score', 'home_score']].fillna(method='ffill')
        game_pbp[['away_score', 'home_score']] = game_pbp[['away_score', 'home_score']].fillna(0)

        # assign a matchup number for each matchup
        import itertools
        matchup_num = 1
        game_pbp['matchup_num'] = 1
        for index, row in game_pbp[1:].iterrows():
            home_cols = list(itertools.chain(*[['home_player{}_id'.format(i)] for i in range(1, 6)]))
            away_cols = list(itertools.chain(*[['home_player{}_id'.format(i)] for i in range(1, 6)]))
            compare_cols = home_cols + away_cols
            # compare the matchups to determine a sub.
            if set(row[compare_cols]) != set(game_pbp.ix[index-1, compare_cols]):
                matchup_num += 1
                game_pbp.ix[index:, 'matchup_num'] = matchup_num

        def compute_stats(group):
            home_team = group.iloc[0].home_team
            away_team = group.iloc[0].away_team

            home_team_msk = group['team'] == home_team
            away_team_msk = group['team'] == away_team

            before_ptd = group.iloc[0].home_score - group.iloc[0].away_score
            after_ptd = group.iloc[-1].home_score - group.iloc[-1].away_score

            FGA = ((group['event_type'] == 'shot made') | (group['event_type'] == 'shot missed'))
            OREB = ((group['event_type'] == 'offensive rebound'))
            TOV = ((group['event_type'] == 'turnover'))
            FT_GROUPS = ((group['event_type'] == 'free throw') | (group['num'] == 1))

            away_possessions = len(group[(FGA & away_team_msk)]) \
                - len(group[OREB & away_team_msk]) \
                + len(group[TOV & away_team_msk]) \
                + len(group[FT_GROUPS & away_team_msk])

            home_possessions = len(group[FGA & home_team_msk]) \
                - len(group[OREB & home_team_msk]) \
                + len(group[TOV & home_team_msk]) \
                + len(group[FT_GROUPS & home_team_msk])

            elapsed_time = group.iloc[-1].overall_elapsed_time - group.iloc[0].overall_elapsed_time

            home_cols = list(itertools.chain(*[['home_player{}_id'.format(i), 'home_player{}_name'.format(i)] for i in range(1, 6)]))
            away_cols = list(itertools.chain(*[['away_player{}_id'.format(i), 'away_player{}_name'.format(i)] for i in range(1, 6)]))

            out_cols = {'StartPlayID': group.iloc[0].play_id,
                        'EndPlayID': group.iloc[-1].play_id,
                        'PointDifference': after_ptd - before_ptd,
                        'AwayPossessions': away_possessions,
                        'HomePossessions': home_possessions,
                        'ElapsedTime': elapsed_time}

            for col in home_cols + away_cols + ['game_id']:
                out_cols[col] = group.iloc[0][col]

            return pd.DataFrame([out_cols])

        grouped = game_pbp.groupby('matchup_num')

        out_file = self.output().open('w')
        grouped.apply(compute_stats).reset_index().to_csv(out_file)
        out_file.close()

    def output(self):
        return luigi.LocalTarget(('data/matchups/' + self.output_file_format).format(game_id=self.game_id))


class SeasonMatchups(luigi.WrapperTask):
    season = luigi.parameter.Parameter()

    def requires(self):
        from statsnba.utils import make_season
        season = make_season(int(self.season))
        game_ids = get_season_game_ids(season)

        for g in game_ids:
            yield PbPToMatchups(game_id=g.strip())


class AggregateSeasonMatchups(luigi.Task):
    season = luigi.parameter.Parameter()
    ignore_failed = luigi.parameter.BoolParameter(default=True)

    def requires(self):
        from statsnba.utils import make_season
        season = make_season(int(self.season))
        game_ids = get_season_game_ids(season)
        matchups = []
        for game_id in game_ids:
            matchup = PbPToMatchups(game_id=game_id.strip())
            if matchup.output().exists():
                matchups.append(matchup)
        return matchups

    def run(self):
        matchups = [pd.read_csv(f.open('r')) for f in self.input()]
        df = pd.concat(matchups)
        with self.output().open('w') as out_file:
            df.to_csv(out_file)

    def output(self):
        return luigi.LocalTarget('data/aggregated_matchups_%s.csv' % self.season)
