import time
import json
import requests
import re
import nltk
from wordcloud import WordCloud
# import matplotlib.pyplot as plt
from PIL import Image

import logging
logging.basicConfig(level=logging.DEBUG)



import nytimesarticle as nyt

import Util

API_QUERY_RATE = 5 # per second
NYT_CACHE = './nyt.cache'

class NytApi():
    def __init__(self, accountKey=None):
        if( accountKey==None ):
            with open('APIKEY.txt', 'r') as f:
                accountKey = f.readline().strip()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(self.__class__.__name__+'Initialised')
        self.cache = Util.FileDict(NYT_CACHE)
        self.api = nyt.articleAPI(accountKey)
        self.API_FIELDS = ['headline', 'pub_date', 'abstract', 'snippet', 'lead_paragraph']

    def search(self, date, query_word='president', num_pages=5):
        cache_key = str( (date, query_word, num_pages) )
        if(not self.cache.has_key(cache_key)):
            all_articles = []
            for i in range(num_pages):
                result = self.api.search(  q=query_word,
                            begin_date=date,
                            fl=self.API_FIELDS,
                            sort='oldest',
                            page=i )
                time.sleep(4 * 1.0/API_QUERY_RATE)
                self._last_result = result
                try:
                    all_articles.extend(result['response']['docs'])
                except Exception, e:
                    self.logger.exception(e)
            self.cache[cache_key] = all_articles
        return self.cache[cache_key]

PS = nltk.stem.PorterStemmer()
NORMALIZE = lambda w: PS.stem(w.strip()).lower()
STOPWORDS = [NORMALIZE(w) for w in open('stopwords.txt','r')]

class NewsBubble():
    def __init__(self):
        self.a = NytApi()
        self.wcf = WordCloud(stopwords=STOPWORDS)

        self.cache = {}

        self.text = []
        self.words = []

    def getWords(self,sd, ed, query_word, num_pages=5):
        cache_key = str((sd, ed, query_word, num_pages))
        if(not self.cache.has_key(cache_key)):
            all_articles = []
            for d in range(sd, ed):
                all_articles.extend(self.a.search(d, query_word, num_pages))
            text = [article['headline']['main'] for article in all_articles]
            words = re.findall('\w+', '. '.join(text))
            stems = [NORMALIZE(w) for w in words]
            stem2word = dict(zip(stems, words))
            words2 = map(lambda x: stem2word[x], stems)
            self.cache[cache_key] = words2
        return self.cache[cache_key]

    def makeCloud(self,sd, ed, query_word, num_pages=5, save=True):
        words = self.getWords(sd, ed, query_word, num_pages)
        wc = self.wcf.generate(' '.join(words))
        wci = wc.to_image()
        if(save):
            cache_key = str((sd, ed, query_word, num_pages))
            wci.save('./imgs/'+Util.fsSafeString(cache_key)+'.png', format='png')
        return wci

