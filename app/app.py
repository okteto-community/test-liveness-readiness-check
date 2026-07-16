#!/usr/bin/env python3
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))
HEALTH_PATH = os.environ.get("HEALTH_PATH", "/status")
HEALTHY_AFTER = float(os.environ.get("HEALTHY_AFTER", "-1"))

BOOT_ID = uuid.uuid4().hex[:8]
START = time.time()
_requests = 0


def _healthy():
    return HEALTHY_AFTER >= 0 and (time.time() - START) >= HEALTHY_AFTER


def _log(msg):
    sys.stderr.write(f"[app boot={BOOT_ID}] {msg}\n")
    sys.stderr.flush()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _requests
        if self.path.split("?")[0] == HEALTH_PATH:
            _requests += 1
            elapsed = time.time() - START
            body, code = (b"OK\n", 200) if _healthy() else (b"Service Unavailable\n", 503)
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            _log(f"healthcheck #{_requests} {self.path} -> {code} (uptime={elapsed:0.1f}s)")
        else:
            body = f"app boot={BOOT_ID}\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    _log(f"starting on :{PORT}, health_path={HEALTH_PATH}, healthy_after={HEALTHY_AFTER}s")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
