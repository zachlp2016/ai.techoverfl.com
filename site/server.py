import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent


class SiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".mobileconfig": "application/x-apple-aspen-config",
    }

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return

        if self.path == "/downloads/tof-ai-app.mobileconfig":
            connector = SITE_ROOT / "downloads" / "tof-ai-app.mobileconfig"
            if not connector.exists():
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"The iPhone connector file has not been uploaded yet.\n"
                )
                return

        super().do_GET()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    handler = partial(SiteHandler, directory=SITE_ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"Serving TOF AI Dashboard on http://0.0.0.0:{port}")
    server.serve_forever()
