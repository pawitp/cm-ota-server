import logging
from google.appengine.api import urlfetch


def get_file(filename):
    try:
        # CloudFlare-backed host
        url = 'http://cm-dl.pawitp.net/%s' % filename

        # Check existence
        result = urlfetch.fetch(url, method=urlfetch.HEAD)
        if result.status_code == 200:
            return url
        else:
            return None
    except Exception, e:
        logging.error("Unable to query CDN " + str(e))
        return None
