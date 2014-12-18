import logging
import urllib2
from google.appengine.api import memcache

MEMCACHE_KEY_XML = "xml_41223"
MEMCACHE_KEY_THREAD = "thread_41223"
MEMCACHE_TIMEOUT = 5 * 60  # 5 minutes


def get_folder_info(device):
    if device != "i9082":
        raise Exception("Invalid device")

    return _fetch_memcache('http://d-h.st/api/folder/content?folder_id=41223', MEMCACHE_KEY_XML)


def get_thread(device, rom):
    if device != "i9082" or rom != "cm-12":
        raise Exception("Unknown device or version")

    return _fetch_memcache('http://forum.xda-developers.com/galaxy-grand-duos/development/rom-cm-12-0-galaxy-grand-duos-i9082-t2942255', MEMCACHE_KEY_THREAD)


def _fetch_memcache(url, cache_key):
    data = memcache.get(cache_key)
    if data:
        return data

    data = urllib2.urlopen(url).read()
    logging.info("Fetching:" + url)
    memcache.add(key=cache_key, value=data, time=MEMCACHE_TIMEOUT)
    return data
