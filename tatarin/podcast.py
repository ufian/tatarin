import re
import datetime as dt

import requests as r
from dateutil import parser as dp

class Podcast(object):
    FEED_URL = "https://feeds.feedburner.com/rosnovsky"

    CACHE = None
    CACHE_DT = None

    re_pubdate = re.compile('<pubDate>(.*)</pubDate>')
    re_title = re.compile('<title>(.*)</title>')

    def __init__(self):
        self._update_cache()
        self._parse_feed()

    def _update_cache(self):
        if Podcast.CACHE_DT is not None and (dt.datetime.now() - Podcast.CACHE_DT) < dt.timedelta(hours=8):
            return

        try:
            req = r.get(Podcast.FEED_URL)

            if '<pubDate>' not in req.text:
                return

            Podcast.CACHE = req.text
            Podcast.CACHE_DT = dt.datetime.now()

        except:
            return

    def _parse_feed(self):
        self.podcasts = list()

        if Podcast.CACHE is None:
            return

        parts = Podcast.CACHE.split('<item>')[1:]

        for part in parts:
            pubdate = self.re_pubdate.search(part)
            title = self.re_title.search(part)

            if not pubdate or not title:
                continue

            pubdate = pubdate.group(1)
            title = title.group(1)

            try:
                pubdate = dp.parse(pubdate)
            except:
                continue

            self.podcasts.append((pubdate, title))

    def info(self, shift=0):
        if len(self.podcasts) == 0:
            return dt.datetime.now() - dt.timedelta(days=60), "Feed unavailable"

        if shift >= len(self.podcasts):
            return self.podcasts[-1]

        return self.podcasts[shift]

    def info_number(self, number=0):
        if len(self.podcasts) == 0:
            return dt.datetime.now() - dt.timedelta(days=60), "Feed unavailable"

        number_str = "#{0:03d}".format(number)

        for pubdate, title in self.podcasts:
            if number_str in title:
                return pubdate, title

        return self.info()
