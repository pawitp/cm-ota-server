#!/usr/bin/env python
import json
import logging
import os

import webapp2

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
            end_str = 'For CM changelog'
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


class ApiHandler(webapp2.RequestHandler):
    def post(self):
        try:
            req = json.loads(self.request.body)
            if req['method'] != "get_all_builds":
                raise Exception("Unknown method")

            vendor, device, rom, date = backend.extract_version(req['params']['source_incremental'])
            folder_info = backend.get_folder_info(device, rom)
            info = []
            for f in folder_info:
                filename = f['filename']
                if not filename.startswith("cm-12"):
                    continue
                if "delta" in filename:
                    continue

                rom, version, date, channel, device = filename.strip(".zip").split("-")
                version = version.replace(".", "-")
                build_id = 'pawitp.%s.%s-%s.%s' % (device, rom, version, date)
                rom_version = "%s-%s" % (rom, version)

                download_url = localstore.get_file(filename, rom_version)
                if not download_url:
                    download_url = f['url']

                info.append({
                    'incremental': build_id,
                    'api_level': backend.api_level_from_rom(rom_version),
                    'url': download_url,
                    'timestamp': backend.timestamp_from_build_date(date),
                    'md5sum': f['md5sum'],
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
            vendor, device, rom, date = backend.extract_version(req['source_incremental'])
            target_date = backend.extract_version(req['target_incremental'])[3]
            target_file = "%s-%s_from_%s_delta-UNOFFICIAL-%s.zip" % (backend.get_rom_filename(rom), target_date, date, device)
            logging.info("Looking for " + target_file)

            folder_info = backend.get_folder_info(device, rom)
            info = {}
            for f in folder_info:
                filename = f['filename']
                if filename != target_file:
                    continue

                # Check local GCS bucket
                download_url = localstore.get_file(filename, rom)
                if not download_url:
                    download_url = f['url']

                logging.info("Returning: " + download_url)

                info = {
                    'filename': filename,
                    'download_url': download_url,
                    'md5sum': f['md5sum'],
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
], debug=True)
