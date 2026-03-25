#!/usr/bin/env python3
"""Proxy server for OK fuel prices — Live Benzinpriser."""

import http.server
import urllib.request
import urllib.error
import json
import os

PORT = 3000
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
OK_API_URL = "https://mobility-prices.ok.dk/api/v1/fuel-prices"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        # Intercept data.json to always serve fresh data locally
        if self.path in ("/data.json", "/data.json?"):
            self.serve_data_json()
        else:
            super().do_GET()

    def serve_data_json(self):
        """Fetch live data from OK API and return it as data.json."""
        try:
            req = urllib.request.Request(
                OK_API_URL,
                headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            raw["fetched_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
            body = json.dumps(raw, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.URLError as e:
            body = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silence request logs


if __name__ == "__main__":
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        print(f"  Live Benzinpriser running at http://localhost:{PORT}")
        httpd.serve_forever()
