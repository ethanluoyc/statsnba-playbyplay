from gevent.pool import Pool
from gevent.queue import Queue
import grequests
import logging

logger = logging.getLogger(__name__)


class Fetcher(object):
    """ Fetcher class for downloading resources online

    It uses grequests to support simultaneous downloads of multiple resources
    """

    # headers to allow correct return of data.
    # referenced from py-Goldsberry
    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'\
        ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 '\
        'Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9'\
        ',image/webp,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive'
    }

    def __init__(self, size=3, api=None):
        self.size = size
        self.responses = []
        self.api = api

    def fetch(self, urls):
        """Start to fetch the urls

        :param urls the list of urls to download
        :rtype None access the fetched resources by self.get()
        """
        def after_download(url):
            # need kargs for correct working
            # http://stackoverflow.com/questions/17977525/\
            # how-to-make-asynchronous-http-get-requests-in-python-and-pass-response-object-to
            def res_func(res, **kargs):
                if self.validate(res):
                    self.api.post_download(res) # TODO factor out this maybe?
                    logger.info('Downloaded ' + url)
                else:
                    logger.info('Failed to download ' + url)
            return res_func

        def _exception_handler(request, exception):
            logger.exception(request.url)
            logger.exception(exception)

        # TODO use pool and queue from gevent for complete non-blocking
        rqs = [grequests.get(u, headers=Fetcher.headers, callback=after_download(u)) for u in urls]

        self.responses = grequests.imap(rqs, size=self.size, exception_handler=_exception_handler)

    def validate(self, res):
        """validate the response"""
        if res.status_code == 200:
            return True
        else:
            return False

    def get(self):
        rs = []
        for r in self.responses:
            if r:
              rs.append(r.json())
        return rs
