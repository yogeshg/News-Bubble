import time
import json
import requests
import re
import nltk
import urlparse
from wordcloud import WordCloud
from collections import Counter

# import matplotlib.pyplot as plt
from PIL import Image
from flask import Flask, render_template, request

import logging
logging.basicConfig(level=logging.INFO )


import nytimesarticle as nyt

import Util

API_QUERY_RATE = 5 # per second
NYT_CACHE = './nyt-dir.cache'

if __name__ == '__main__':
    application = Flask(__name__)

class NytApi():
    def __init__(self, accountKey=None):
        if( accountKey==None ):
            with open('APIKEY.txt', 'r') as f:
                accountKey = f.readline().strip()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(self.__class__.__name__+'Initialised')
        self.cache = Util.DirDict(NYT_CACHE, valueDumper=json.dumps, valueLoader=json.loads)
        self.api = nyt.articleAPI(accountKey)
        self.API_FIELDS = ['headline', 'pub_date', 'abstract', 'snippet', 'lead_paragraph']

    def search(self, date, query_word='president', num_pages=5):
        all_articles = []
        try:
            cache_key = str( (date, query_word, num_pages) )
            if(not self.cache.has_key(cache_key)):
                for i in range(num_pages):
                    result = self.api.search(q=query_word, begin_date=date, fl=self.API_FIELDS, sort='oldest', page=i )
                    time.sleep(4 * 1.0/API_QUERY_RATE)
                    self._last_result = result
                    try:
                        all_articles.extend(result['response']['docs'])
                    except Exception, e:
                        self.logger.exception(e)
                        self.logger.exception(str(self._last_result))
                self.cache[cache_key] = all_articles
            all_articles = self.cache[cache_key]
        except Exception as e:
            self.logger.exception( e )
        return all_articles

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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(self.__class__.__name__+'Initialised')

    def getWords(self,sd, ed, query_word, num_pages=1):
        self.logger.info('getWords'+str((sd, ed, query_word, num_pages)))
        cache_key = self.getCacheKey(sd, ed, query_word, num_pages)
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

    def getCacheKey(self, sd, ed, query_word, num_pages):
        return str((sd, ed, query_word, num_pages))

    def getImagePath(self, sd, ed, query_word, num_pages):
        cache_key = self.getCacheKey(sd, ed, query_word, num_pages)
        img_file='static/'+Util.fsSafeString(cache_key)+'.png'
        return img_file

    def makeCloud(self,sd, ed, query_word, num_pages=1, save=True):
        self.logger.info('makeCloud'+str((sd, ed, query_word, num_pages, save)))
        words = self.getWords(sd, ed, query_word, num_pages)
        wc = self.wcf.generate(' '.join(words))
        wci = wc.to_image()
        if(save):
            img_file = self.getImagePath(sd, ed, query_word, num_pages)
            logging.info('saving... '+img_file)
            wci.save( img_file , format='png')
        return words

@application.route('/')
def default():
    return render_template('index.html', start=20161101, end=20161108, query='president', img='i1', freq='[]')

@application.route('/search')
# @application.route('/')
def main():
    user = request.args.get('user')
    logging.info('querystring : '+str(request.args))
    sd = int(request.args.get('begin_date'))
    ed = int(request.args.get('end_date'))
    qw = request.args.get('q')
    np = int(request.args.get('np', 1))
    app.makeCloud(sd, ed, qw, num_pages=np) # make async
    words = []
    freq = dict(Counter(words))
    freq2 = []
    for k,v in freq.iteritems():
        freq2.append({'text':k, 'weight':v})
    string = json.dumps(freq2)
    print string
    img_file = app.getImagePath(sd, ed, qw, np)
    return render_template('index.html', start=sd, end=ed, query=qw, img=img_file, freq='[]')

if __name__ == '__main__':
    app=NewsBubble()
    application.run(host='0.0.0.0')

