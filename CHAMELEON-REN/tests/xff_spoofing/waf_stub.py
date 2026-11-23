"""Stub for the Layer 2 WAF: echoes the headers it receives as JSON.

Lets the integration test see exactly what Nginx + the Stimulus Engine forward
downstream (X-Real-IP, X-Forwarded-For, X-Chameleon-Target, ...).
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Echo(BaseHTTPRequestHandler):
    def _reply(self):
        body = json.dumps({k.lower(): v for k, v in self.headers.items()}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = do_PUT = do_DELETE = do_OPTIONS = do_PATCH = _reply

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Echo).serve_forever()
