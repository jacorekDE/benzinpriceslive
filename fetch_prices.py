#!/usr/bin/env python3
"""
Fetches OK fuel prices for Copenhagen region and writes data.json.
Run by GitHub Actions every hour.
"""

import urllib.request
import json
import sys
from datetime import datetime, timezone

OK_API_URL = "https://mobility-prices.ok.dk/api/v1/fuel-prices"
OUTPUT_FILE = "data.json"

def main():
    print(f"Fetching {OK_API_URL} ...")
    try:
        req = urllib.request.Request(OK_API_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Inject a top-level timestamp so the page can show when data was last fetched
    data["fetched_at"] = datetime.now(timezone.utc).isoformat()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    items = data.get("items", [])
    print(f"OK — {len(items)} stations written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
