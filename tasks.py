import logging
from google.appengine.api import memcache
import webapp2
import localstore


class CacheHandler(webapp2.RequestHandler):
    def post(self):
        filename = self.request.get('filename')
        url = self.request.get('url')
        md5sum = self.request.get('md5sum')

        # XXX: memcache as pseudo-mutex
        key = 'fetch:' + filename
        if memcache.get(key):
            logging.debug("Not caching " + filename)
        else:
            memcache.add(key=key, value=1, time=600)  # Try again in 10 minutes if fail
            localstore.try_cache(filename, url, md5sum)


app = webapp2.WSGIApplication([
    ('/tasks/cache', CacheHandler),
], debug=True)
