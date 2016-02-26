# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class StatsnbaItem(scrapy.Item):
    """
        It conforms to the API response from stats.nba.com
    """
    resource = scrapy.Field()
    parameters = scrapy.Field()
    resultSets = scrapy.Field()
