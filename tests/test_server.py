import http.client
import importlib.util
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path


SERVER_PATH = Path(__file__).resolve().parents[1] / "site" / "server.py"
SERVER_SPEC = importlib.util.spec_from_file_location("dashboard_server", SERVER_PATH)
dashboard_server = importlib.util.module_from_spec(SERVER_SPEC)
SERVER_SPEC.loader.exec_module(dashboard_server)


class DashboardServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = partial(
            dashboard_server.SiteHandler,
            directory=dashboard_server.SITE_ROOT,
        )
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
            timeout=3,
        )
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response, body

    def test_health_endpoint(self):
        response, body = self.request("/health")

        self.assertEqual(200, response.status)
        self.assertEqual(b"ok\n", body)

    def test_status_page(self):
        response, body = self.request("/status.html")

        self.assertEqual(200, response.status)
        self.assertIn(b"Public gateway online", body)

    def test_missing_mobile_connector_has_clear_response(self):
        response, body = self.request("/downloads/tof-ai-app.mobileconfig")

        self.assertEqual(404, response.status)
        self.assertIn(b"has not been uploaded yet", body)

    def test_server_source_is_not_public(self):
        response, _body = self.request("/server.py")

        self.assertEqual(404, response.status)

    def test_directory_listing_is_disabled(self):
        response, _body = self.request("/downloads/")

        self.assertEqual(404, response.status)

    def test_well_known_directory_is_allowed(self):
        self.assertFalse(
            dashboard_server.SiteHandler.forbidden_path(
                "/.well-known/apple-app-site-association"
            )
        )


if __name__ == "__main__":
    unittest.main()
