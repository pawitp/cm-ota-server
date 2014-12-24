#!/usr/bin/env python
import json
import logging
import os
from google.appengine.api import memcache
from google.appengine.api.blobstore import blobstore
from google.appengine.api.taskqueue import taskqueue
from google.appengine.ext.webapp import blobstore_handlers
import webapp2
from xml.etree import ElementTree
import backend
import localstore


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect("http://forum.xda-developers.com/galaxy-grand-duos/development/rom-cm-12-0-galaxy-grand-duos-i9082-t2942255/")


class ChangelogHandler(webapp2.RequestHandler):
    def get(self, build_id=''):
        try:
            vendor, device, rom, date = build_id.split('.')
            date = int(date)
            thread = backend.get_thread(device, rom)
            stage = 0
            output = []
            date_found = False

            start_str = '<font size="5"><b>Changelog</b></font><br />'
            end_str = '<font size="5"><b>FAQ</b></font><br />'
            changelog = thread[thread.index(start_str) + len(start_str):thread.index(end_str)]
            changelog = changelog.replace("\n", "")
            changelog = changelog.replace("\r", "")
            for line in changelog.split("<br />"):
                if len(line) == 0:
                    continue

                line_date = int(line.split(":")[0])
                if line_date > date:
                    # Future build
                    continue
                elif line_date == date:
                    date_found = True
                output.append(line)
                if len(output) > 10:
                    break
            if not date_found:
                raise Exception("No change log found for date %d." % date)
            self.response.write("\n\n".join(output))
        except Exception, e:
            logging.error("Exception " + str(e))
            self.response.write("Change log not available.\n" + str(e))


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, filename):
        try:
            if not localstore.get_file(filename):
                self.error(404)
                self.response.out.write("Not Found")
                return

            memcache_key = 'gs:' + filename
            blob_key = memcache.get(memcache_key)
            if not blob_key:
                blob_key = blobstore.create_gs_key('/gs' + localstore.get_gcs_filename(filename))
                memcache.add(key=memcache_key, value=blob_key, time=864000)
            self.send_blob(blob_key, save_as=filename)
        except Exception, e:
            logging.error("Exception " + str(e))


class ApiHandler(webapp2.RequestHandler):
    def post(self):
        try:
            req = json.loads(self.request.body)
            if req['method'] != "get_all_builds":
                raise Exception("Unknown method")

            xml_str = backend.get_folder_info(req['params']['device'])
            xml = ElementTree.ElementTree(ElementTree.fromstring(xml_str))
            info = []
            for f in xml.findall(".//file_info"):
                filename = f.find('filename').text
                if not filename.startswith("cm-12"):
                    continue
                if "delta" in filename:
                    continue

                rom, version, date, channel, device = filename.strip(".zip").split("-")
                build_id = 'pawitp.%s.%s-%s.%s' % (device, rom, version, date)

                info.append({
                    'incremental': build_id,
                    'api_level': 21,
                    'url': f.find('direct_download_url').text,
                    'timestamp': backend.timestamp_from_build_date(date),
                    'md5sum': f.find('md5sum').text,
                    'changes': 'https://%s/changelog/%s' % (os.environ['HTTP_HOST'], build_id),
                    'channel': 'nightly',
                    'filename': filename,
                })
            result = {
                'id': None,
                'result': info,
                'error': None,
            }
            self.response.write(json.dumps(result))
        except Exception, e:
            logging.error("Exception " + str(e))
            self.response.write(json.dumps({'id': None, 'error': str(e)}))


class DeltaHandler(webapp2.RequestHandler):
    def post(self):
        try:
            req = json.loads(self.request.body)

            # pawitp.i9082.cm-12.20141216
            vendor, device, rom, date = req['source_incremental'].split(".")
            target_date = req['target_incremental'].split(".")[3]
            target_file = "%s-%s_from_%s_delta-UNOFFICIAL-%s.zip" % (rom, target_date, date, device)
            logging.info("Looking for " + target_file)

            xml_str = backend.get_folder_info(device)
            xml = ElementTree.ElementTree(ElementTree.fromstring(xml_str))
            info = {}
            for f in xml.findall(".//file_info"):
                filename = f.find('filename').text
                if filename != target_file:
                    continue

                md5sum = f.find('md5sum').text

                # Check local GCS bucket
                download_url = localstore.get_file(filename)
                if not download_url:
                    download_url = f.find('direct_download_url').text
                    taskqueue.add(url='/tasks/cache',
                                  params={'filename': filename, 'url': download_url, 'md5sum': md5sum})

                logging.info("Returning: " + download_url)

                info = {
                    'filename': filename,
                    'download_url': download_url,
                    'md5sum': md5sum,
                    'date_created_unix': backend.timestamp_from_build_date(target_date),
                    'incremental': req['target_incremental'],
                }
                break

            self.response.write(json.dumps(info))
        except Exception, e:
            logging.error("Exception " + str(e))
            self.response.write(json.dumps({'errors': str(e)}))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    webapp2.Route('/changelog/<build_id>', handler=ChangelogHandler),
    ('/api', ApiHandler),
    ('/api/v1/build/get_delta', DeltaHandler),
    webapp2.Route('/dl/<filename>', handler=DownloadHandler),
], debug=True)
