import os
import unittest
import json
import time

from google.appengine.ext import testbed
import webtest

import main


class AppTest(unittest.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(main.app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()

        os.environ['TZ'] = 'UTC'
        time.tzset()

    def tearDown(self):
        self.testbed.deactivate()

    def testChangeLog12_0(self):
        response = self.testapp.get("/changelog/pawitp.i9082.cm-12.20141120")
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body,
                         "20141120: Fixed .wav playback, video recording, off-mode charging, &quot;mount /data&quot; error in install script, low call volume\n\n20141116: Initial release")

    def testChangeLog12_1(self):
        response = self.testapp.get("/changelog/pawitp.i9082.cm-12-1.20150410")
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body,
                         "20150410: Upstream merge\n\n20150408: Upstream merge\n\n20150405: Initial release")

    def testChangeLogNotFound(self):
        response = self.testapp.get("/changelog/pawitp.i9082.cm-12-1.20000101")
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, "Change log not available.\nNo change log found for date 20000101.")

    def testApiRequest12_0(self):
        response = self.testapp.post("/api", """
{
    "method": "get_all_builds",
    "params": {
        "device": "i9082",
        "channels": [
            "nightly"
        ],
        "source_incremental": "pawitp.i9082.cm-12.20150711"
    }
}
        """)
        self.assertEqual(response.status_int, 200)

        jsonResp = json.loads(response.body)
        self.assertIsNone(jsonResp["id"])
        self.assertIsNone(jsonResp["error"])

        # Only check the first result for now
        entry = jsonResp["result"][0]
        self.assertEqual(entry["timestamp"], "1416096000")
        self.assertEqual(entry["url"],
                         "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.0/cm-12-20141116-UNOFFICIAL-i9082.zip")
        self.assertEqual(entry["incremental"], "pawitp.i9082.cm-12.20141116")
        self.assertEqual(entry["channel"], "nightly")
        self.assertEqual(entry["changes"], "https://testbed.example.com/changelog/pawitp.i9082.cm-12.20141116")
        self.assertEqual(entry["filename"], "cm-12-20141116-UNOFFICIAL-i9082.zip")
        self.assertEqual(entry["api_level"], 21)
        self.assertEqual(entry["md5sum"], "9563a7821b69a0553ffc39176f38d9c4")

    def testApiRequest12_1(self):
        response = self.testapp.post("/api", """
{
    "method": "get_all_builds",
    "params": {
        "device": "i9082",
        "channels": [
            "nightly"
        ],
        "source_incremental": "pawitp.i9082.cm-12-1.20150711"
    }
}
        """)
        self.assertEqual(response.status_int, 200)

        jsonResp = json.loads(response.body)
        self.assertIsNone(jsonResp["id"])
        self.assertIsNone(jsonResp["error"])

        # Only check the first result for now
        entry = jsonResp["result"][0]
        self.assertEqual(entry["timestamp"], "1428192000")
        self.assertEqual(entry["url"],
                         "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.1/cm-12.1-20150405-UNOFFICIAL-i9082.zip")
        self.assertEqual(entry["incremental"], "pawitp.i9082.cm-12-1.20150405")
        self.assertEqual(entry["channel"], "nightly")
        self.assertEqual(entry["changes"], "https://testbed.example.com/changelog/pawitp.i9082.cm-12-1.20150405")
        self.assertEqual(entry["filename"], "cm-12.1-20150405-UNOFFICIAL-i9082.zip")
        self.assertEqual(entry["api_level"], 22)
        self.assertEqual(entry["md5sum"], "eef8aa7686ca0ce2eada6d81b94e74d3")

    def testDeltaRequest12_0(self):
        response = self.testapp.post("/api/v1/build/get_delta", """
{
    "source_incremental": "pawitp.i9082.cm-12.20150319",
    "target_incremental": "pawitp.i9082.cm-12.20150320"
}
        """)
        self.assertEqual(response.status_int, 200)

        jsonResp = json.loads(response.body)
        self.assertEqual(jsonResp["incremental"], "pawitp.i9082.cm-12.20150320")
        self.assertEqual(jsonResp["md5sum"], "016a46391ad69fd0fb232886a78fa31f")
        self.assertEqual(jsonResp["date_created_unix"], "1426809600")
        self.assertEqual(jsonResp["download_url"],
                         "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.0/cm-12-20150320_from_20150319_delta-UNOFFICIAL-i9082.zip")
        self.assertEqual(jsonResp["filename"], "cm-12-20150320_from_20150319_delta-UNOFFICIAL-i9082.zip")

    def testDeltaRequest12_1(self):
        response = self.testapp.post("/api/v1/build/get_delta", """
{
    "source_incremental": "pawitp.i9082.cm-12-1.20150703",
    "target_incremental": "pawitp.i9082.cm-12-1.20150711"
}
        """)
        self.assertEqual(response.status_int, 200)

        jsonResp = json.loads(response.body)
        self.assertEqual(jsonResp["incremental"], "pawitp.i9082.cm-12-1.20150711")
        self.assertEqual(jsonResp["md5sum"], "2f22764b06dc4306c8a9915fefa1c701")
        self.assertEqual(jsonResp["date_created_unix"], "1436572800")
        self.assertEqual(jsonResp["download_url"],
                         "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.1/cm-12.1-20150711_from_20150703_delta-UNOFFICIAL-i9082.zip")
        self.assertEqual(jsonResp["filename"], "cm-12.1-20150711_from_20150703_delta-UNOFFICIAL-i9082.zip")

    def testDeltaRequestNotFound(self):
        response = self.testapp.post("/api/v1/build/get_delta", """
{
    "source_incremental": "pawitp.i9082.cm-12.20150319",
    "target_incremental": "pawitp.i9082.cm-12.20150330"
}
        """)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body, "{}")
