import hashlib
import logging
import os
import urllib2
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
            return 'https://storage.googleapis.com%s' % gcs_filename
    except gcs.errors.NotFoundError, e:
        return None


def try_cache(filename, url, md5sum):
    logging.info("Trying to cache " + url)
    gcs_filename = _get_gcs_filename(filename)

    response = urllib2.urlopen(url)
    data = response.read()
    info = response.info()
    local_md5 = hashlib.md5(data).hexdigest()

    if local_md5 != md5sum:
        logging.error("MD5 sum mismatch expected: %s got: %s" % (md5sum, local_md5))

    f = gcs.open(gcs_filename, 'w', info.type)
    f.write(data)
    f.close()

    logging.info("Successfully cached %s with md5 %s and content-ype %s" % (filename, local_md5, info.type))
