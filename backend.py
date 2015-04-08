from datetime import datetime
import logging
import urllib2
from google.appengine.api import memcache

MEMCACHE_TIMEOUT = 20 * 60  # 20 minutes


def extract_version(rev):
    # pawitp.i9082.cm-12.20141216
    vendor, device, rom, date = rev.split(".")

    if date == "20150404" and rom == "cm-12":
        # SPECIAL CASE: problem in distributed build (which was actually dated 20150405 on the outside)
        date = "20150405"
        rom = "cm-12-1"

    return vendor, device, rom, date


def get_folder_info(device, rom):
    if device != "i9082":
        raise Exception("Unknown device")

    if rom == "cm-12":
        return _fetch_memcache('http://d-h.st/api/folder/content?folder_id=41223')
    elif rom == "cm-12-1":
        return _fetch_memcache('http://d-h.st/api/folder/content?folder_id=44634')
    else:
        raise Exception("Unknown version")


def get_thread(device, rom):
    if device != "i9082":
        raise Exception("Unknown device")

    if rom == "cm-12":
        return _fetch_memcache('http://forum.xda-developers.com/galaxy-grand-duos/development/rom-cm-12-0-galaxy-grand-duos-i9082-t2942255')
    elif rom == "cm-12-1":
        return _fetch_memcache('http://forum.xda-developers.com/galaxy-grand-duos/development/rom-cm-12-1-galaxy-grand-duos-i9082-t3073108')
    else:
        raise Exception("Unknown version")


def _fetch_memcache(url):
    cache_key = "url:%s" % url
    data = memcache.get(cache_key)
    if data:
        return data

    data = urllib2.urlopen(url).read()
    logging.info("Fetching:" + url)
    memcache.add(key=cache_key, value=data, time=MEMCACHE_TIMEOUT)
    return data


def timestamp_from_build_date(build_date):
    return datetime.strptime(build_date, "%Y%m%d").strftime("%s")
