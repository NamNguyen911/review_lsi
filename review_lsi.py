import os

import cherrypy
from pymongo import MongoClient
from bson.objectid import ObjectId
import simplejson as json
import requests

cherrypy.server.socket_host = '0.0.0.0'
cherrypy.engine.start()

def to_utf8(text):
    if isinstance(text, unicode):
        return text.encode('utf8')
    return unicode(text, 'utf8', errors='strict').encode('utf8')

class RelatedArticle(object):
    def __init__(self):
        self._db = MongoClient('localhost').lion_matcher

    @cherrypy.expose
    def index(self):
        links = self._db.link.find().limit(10)
        formatter = '<li><a href="/link?link_id={0}">{1}</a></li>'
        items = "".join([formatter.format(l['_id'], l['title']) for l in links])
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
    def link(self, link_id):
        link = self._db.link.find_one({'_id': ObjectId(link_id)})
        item_formatter = """
        <h1 class='title'>
            <a href={0} target='_blank'>{1}</a>
        </h1>
        <p class='body'>{2} </p>
        """
        item = item_formatter.format(
                link['url'], link['title'], link['body'])
        related_content = self.get_relevant_content(link)
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

    @cherrypy.expose
    def content(self, content_id):
        content = self._db.content.find_one({'_id': ObjectId(content_id)})
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
                        <h1 class='title'>
                            <a href={0} target='_blank'>{1}</a>
                        </h1>
                        <p class='body'>{2}</p>
                    </div>
                </div>
            </div>
        </body>
        """.format(content['url'], to_utf8(content['title']), content['body'])
        return content

    def get_relevant_content(self, link):
        relevance = link['relevance']
        scores = dict(zip(relevance['code'][:10], relevance['score'][:10]))

        contents = [(c, scores[c['url_hash']])
            for c in self._db.content.find({'url_hash': {'$in': scores.keys()}})]
        contents.sort(key=lambda x: x[1], reverse=True)

        formatter = "<li><a href='/content?content_id={0}' target='_blank'>{1} {2}</a></li>"
        relevant_content = "".join([formatter.format(c[0]['_id'], to_utf8(c[0]['title']), c[1])
            for c in contents])

        #formatter = "<li><a href='{0}' target='_blank'>{1}-{2}</a></li>"
        #relevant_content = "".join([formatter.format(c[0]['url'], to_utf8(c[0]['title']), c[1])
        #    for c in contents])
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
