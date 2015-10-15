# coding: utf-8
# feed parser
import feedparser

class UpworkFeed(object):
    
    def __init__(self, title=None, link=None, date_created=None):



    def parse(self, url=None):
        feed = feedparser.parse(url)
        for x in feed['entries']:
            self.title = x['title']
#TODO:            self.budget = x['']
            self.link = x['link']
            self.date_created = parsedate(x['published'])



