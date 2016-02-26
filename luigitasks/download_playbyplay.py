import subprocess

import luigi

from .dump_game_ids import FindGames


class DownloadPlayByPlay(luigi.Task):
    def requires(self):
        return FindGames()

    def run(self):
        subprocess.call(['scrapy', 'crawl', 'boxscoretraditional', '--loglevel=INFO', '-a', 'gameids_file=data/game_ids.txt'])

    def output(self):
        pass