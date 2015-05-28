import os

import cherrypy
from pymongo import MongoClient
from bson.objectid import ObjectId
import simplejson as json
import requests
from gensim.utils import to_utf8

cherrypy.server.socket_host = '0.0.0.0'
cherrypy.engine.start()

class RelatedArticle(object):
    def __init__(self):
        self._db = MongoClient('localhost').lion_relevant

    @cherrypy.expose
    def index(self):
        articles = self._db.articles.find().skip(10).limit(10)
        formatter = '<li><a href="/article?_id={0}">{1}</a></li>'
        items = "".join([formatter.format(a['_id'], a['title']) for a in articles])
        content = """
        <head>
            <title>Lion Relevant</title>
            <link rel='stylesheet' href='static/css/gia.ui.css'>
            <link rel='stylesheet' href='static/css/nam.css'>
        </head>
        <body>
        <div class='ctn'>
            <div class='rw'>
                <div class='cl'>
                    <h1 class='title mt-30'>Articles</h1>
                    <ul class='articles'>
                    {0}
                    </ul>
                </div>
            </div>
        </div>
        </body>
        """.format(items)
        return content

    @cherrypy.expose
    def article(self, _id):
        article = self._db.articles.find_one({'_id': ObjectId(_id)})
        item_formatter = """
        <h1 class='title'>
            <a href={0} target='_blank'>{1}</a>
        </h1>
        <p class='body'>{2} </p>
        """
        item = item_formatter.format(
                article['url'], article['title'], article['body'])
        related_content = self.get_relevant_content(article)
        content = """
        <head>
            <title>Lion Relevant</title>
            <link rel='stylesheet' href='static/css/gia.ui.css'>
            <link rel='stylesheet' href='static/css/nam.css'>
        </head>
        <body>
            <div class='ctn'>
                <a href='/' id='back'><img src='static/img/back.png'></a>
                <div class='rw'>
                    <div class='cl md-8'>
                        {0}
                    </div>
                    <div class='cl md-4'>
                        <h2 class='block-title'>Related content</h2>
                        <ul class='articles'>
                            {1}
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        """.format(item, related_content)
        return content

    def get_relevant_score(self, article):
        del article['_id']
        article['is_article'] = False
        headers = {'content-type': 'application/json'}
        data = json.dumps(article)
        res = requests.post('http://localhost/relevance',
                data = data,
                headers = headers)
        scores = json.loads(res.text)
        return scores

    def get_relevant_content(self, article):
        relevant_scores = self.get_relevant_score(article)
        scores = dict(zip(relevant_scores['code'][:10], relevant_scores['score'][:10]))

        relevant_articles = [(a, scores[a['url_hash']])
            for a in self._db.articles.find({'url_hash': {'$in': scores.keys()}})]
        relevant_articles.sort(key=lambda x: x[1], reverse=True)

        formatter = "<li><a href='/article?_id={0}' target='_blank'>{1}-{2}</a></li>"
        # relevant_content = "".join([formatter.format(a[0]['_id'], a[0]['title'], a[1])
        #     for a in relevant_articles])
        relevant_content = "".join([formatter.format(a[0]['_id'], to_utf8(a[0]['title']), a[1])
            for a in relevant_articles])
        return relevant_content


if __name__ == "__main__":
    conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './public'
         }
     }
    cherrypy.quickstart(RelatedArticle(), '/', conf)
