import hashlib
import logging
import os
import urllib2
from google.appengine.api import urlfetch
from google.appengine.api.app_identity import app_identity
import cloudstorage as gcs

GCS_BUCKET = app_identity.get_default_gcs_bucket_name()


def _get_gcs_filename(filename):
    return '/%s/%s' % (GCS_BUCKET, filename)


def get_file(filename):
    try:
        gcs_filename = _get_gcs_filename(filename)

        # Check existence (will throw Error if not found)
        gcs.stat(gcs_filename)
        if os.environ['SERVER_SOFTWARE'].startswith('Development'):
            return 'http://%s/_ah/gcs%s' % (os.environ['HTTP_HOST'], gcs_filename)
        else:
            return 'http://storage.googleapis.com%s' % gcs_filename
    except gcs.errors.Error, e:
        logging.error("Unable to query GCS " + str(e))
        return None


def try_cache(filename, url, md5sum):
    logging.info("Trying to cache " + url)
    gcs_filename = _get_gcs_filename(filename)

    urlfetch.set_default_fetch_deadline(60)
    response = urllib2.urlopen(url)
    data = response.read()
    info = response.info()
    local_md5 = hashlib.md5(data).hexdigest()

    if local_md5 != md5sum:
        logging.error("MD5 sum mismatch expected: %s got: %s" % (md5sum, local_md5))

    f = gcs.open(gcs_filename,
                 'w',
                 info.type,
                 {'x-goog-acl': 'public-read',
                  'cache-control': 'public, max-age=31536000, no-transform'})
    f.write(data)
    f.close()

    logging.info("Successfully cached %s with md5 %s and content-type %s" % (filename, local_md5, info.type))
