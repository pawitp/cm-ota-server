from datetime import datetime
import logging
import urllib2

from google.appengine.api import memcache
from lxml import html

MEMCACHE_TIMEOUT = 20 * 60  # 20 minutes


def extract_version(rev):
    # pawitp.i9082.cm-12.20141216
    vendor, device, rom, date = rev.split(".")

    if date == "20150404" and rom == "cm-12":
        # SPECIAL CASE: problem in distributed build (which was actually dated 20150405 on the outside)
        date = "20150405"
        rom = "cm-12-1"

    return vendor, device, rom, date


def get_rom_filename(rom):
    if rom == "cm-12":
        return "cm-12"
    elif rom == "cm-12-1":
        return "cm-12.1"
    raise Exception("Unknown version")


def get_folder_info(device, rom):
    if device != "i9082":
        raise Exception("Unknown device")

    if rom == "cm-12":
        return get_and_parse_folder_info('https://basketbuild.com/devs/pawitp/i9082_cm12.0/')
    elif rom == "cm-12-1":
        return get_and_parse_folder_info('https://basketbuild.com/devs/pawitp/i9082_cm12.1/')
    else:
        raise Exception("Unknown version")


def get_and_parse_folder_info(url):
    cache_key = "folder:%s" % url
    data = memcache.get(cache_key)
    if data:
        return data

    logging.info("Fetching:" + url)
    data = urllib2.urlopen(url).read()

    tree = html.fromstring(data)
    info = []
    for f in tree.cssselect('[itemtype="http://schema.org/SoftwareApplication"]'):
        # Note: URL for basketbuild doesn't actually work. We assume that localstore will always return a value.
        info.append({
            'filename': f.cssselect("[itemprop=name]")[0].text_content().strip(),
            'md5sum': get_md5sum("https://basketbuild.com" + f.cssselect("[itemprop=downloadUrl]")[0].get('href')),
            'url': f.cssselect("[itemprop=downloadUrl]")[0].attrib['href']
        })

    memcache.add(key=cache_key, value=info, time=MEMCACHE_TIMEOUT)
    return info


def get_md5sum(url):
    cache_key = "md5:%s" % url
    data = memcache.get(cache_key)
    if data:
        return data

    logging.info("Fetching:" + url)
    data = urllib2.urlopen(url).read()

    tree = html.fromstring(data)
    md5 = tree.xpath("normalize-space((//*[text() = 'File MD5:']/following-sibling::text())[1])")

    memcache.add(key=cache_key, value=md5)
    return md5


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


def api_level_from_rom(rom):
    if rom == "cm-12":
        return 21
    elif rom == "cm-12-1":
        return 22
    else:
        raise Exception("Unknown version")