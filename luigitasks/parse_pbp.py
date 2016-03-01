import luigi

class ParseEvent(luigi.Task):
    """
        Parse the events scraped by Scrapy
    """
    pass


class ParseMatchups(luigi.Task):
    """
        Generate the matchups for every event scraped based on boxscore info
    """
    pass


class ParsePlayByPlay(luigi.Task):
    def requires(self):
        yield ParseEvent()
        yield ParseMatchups()

    def run(self):
        pass

    def output(self):
        pass
