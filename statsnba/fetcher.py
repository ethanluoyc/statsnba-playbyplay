from gevent.pool import Pool
from gevent.queue import Queue
import requests
import grequests

class Fetcher(object):

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

    def __init__(self, size=10):
        self.size = size
        self.res = None

    def fetch(self, urls):
        """
        """
        def log_download(url):
            # need kargs for correct working
            # http://stackoverflow.com/questions/17977525/how-to-make-asynchronous-http-get-requests-in-python-and-pass-response-object-to
            def real_func(r, **kargs):
                print(url + ' downloaded')
            return real_func
        # use grequests to allow for simultaneous downloads
        rs = [grequests.get(u, headers=Fetcher.headers, callback=log_download(u)) for u in urls]

        self.res = grequests.imap(rs, size=self.size)

    def get(self):
        if not self.res:
            raise Exception('You have not fetched the data!')
        return [r.json() for r in self.res]
