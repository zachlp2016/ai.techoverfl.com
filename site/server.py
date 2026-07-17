import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE_ROOT = Path(__file__).resolve().parent


class SiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".mobileconfig": "application/x-apple-aspen-config",
    }

    def do_GET(self):
        request_path = unquote(urlsplit(self.path).path)

        if request_path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return

        if request_path == "/downloads/tof-ai-app.mobileconfig":
            connector = SITE_ROOT / "downloads" / "tof-ai-app.mobileconfig"
            if not connector.exists():
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"The iPhone connector file has not been uploaded yet.\n"
                )
                return

        if self.forbidden_path(request_path):
            self.send_error(404)
            return

        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    @staticmethod
    def forbidden_path(request_path):
        path = Path(request_path)
        return path.suffix in {".py", ".pyc"} or any(
            part.startswith(".") and part != ".well-known"
            for part in path.parts if part not in {"/", ".", ".."}
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    handler = partial(SiteHandler, directory=SITE_ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"Serving TOF AI Dashboard on http://0.0.0.0:{port}")
    server.serve_forever()
