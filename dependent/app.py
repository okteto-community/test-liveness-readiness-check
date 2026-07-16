#!/usr/bin/env python3
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8081"))


def _log(msg):
    sys.stderr.write(f"[dependent] {msg}\n")
    sys.stderr.flush()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"OK\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    _log("started -- app is healthy, dependency gate opened")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
