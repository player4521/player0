#!/usr/bin/env python3
"""Local preview for dist/ with Cloudflare Pages-like behaviour.

Serves clean URLs (/products/ -> dist/products/index.html), honours the generated
_redirects file, and returns the generated 404 page. Standard library only.

    python tool/serve.py [--port 8791] [--once URL ...]
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def load_redirects() -> list[tuple[str, str, int]]:
    path = DIST / "_redirects"
    if not path.exists():
        return []
    rules = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            code = int(parts[2]) if len(parts) > 2 else 302
            rules.append((parts[0], parts[1], code))
    return rules


class Handler(http.server.SimpleHTTPRequestHandler):
    redirects: list[tuple[str, str, int]] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):  # noqa: N802
        for src, dst, code in self.redirects:
            if self.path == src or self.path == src.rstrip("/"):
                self.send_response(code)
                self.send_header("Location", dst)
                self.end_headers()
                return
        super().do_GET()

    def send_error(self, code, message=None, explain=None):
        page = DIST / "404.html"
        if code == 404 and page.exists():
            body = page.read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()

    if not DIST.is_dir():
        print("dist/ not found - run: python tool/build.py", file=sys.stderr)
        return 1

    Handler.redirects = load_redirects()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"serving dist/ at http://127.0.0.1:{args.port}/  (ctrl-c to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
