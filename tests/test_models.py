import pytest
import luigi
from luigitasks.matchups import AggregateSeasonMatchups


@pytest.fixture(scope='module')
def filter_task(request):
    season_matchup_task = AggregateSeasonMatchups(season='2009', ignore_failed=True)
    filter_data_task = FilterLineupData(lineup_data=season_matchup_task, threshold=0, filter_by_players=False)

    if filter_data_task.output().exists():
        filter_data_task.output().remove()

    luigi.build([filter_data_task], local_scheduler=True)

    def fn():
        print 'Deleting generated Target'
        filter_data_task.output().remove()

    request.addfinalizer(fn)

    return filter_data_task

