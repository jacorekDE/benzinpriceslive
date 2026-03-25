#!/usr/bin/env python3
"""
Fetches OK fuel prices and writes data.json + history.json.
Run by GitHub Actions every hour.
"""

import urllib.request
import json
import sys
from datetime import datetime, timezone

OK_API_URL   = "https://mobility-prices.ok.dk/api/v1/fuel-prices"
DATA_FILE    = "data.json"
HISTORY_FILE = "history.json"
CPH_MIN, CPH_MAX = 1000, 3999
MAX_HISTORY  = 2000  # ~83 days at hourly intervals


def cph_avg(items, keyword):
    prices = [
        p["price"]
        for s in items
        if CPH_MIN <= int(s.get("postal_code") or 0) <= CPH_MAX
        for p in s.get("prices", [])
        if keyword.lower() in p["product_name"].lower()
    ]
    return round(sum(prices) / len(prices), 4) if prices else None


def main():
    print(f"Fetching {OK_API_URL} ...")
    try:
        req = urllib.request.Request(OK_API_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    data["fetched_at"] = datetime.now(timezone.utc).isoformat()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    items = data.get("items", [])
    print(f"OK — {len(items)} stations written to {DATA_FILE}")

    # ── Compute CPH averages and update history.json ──────────────────────────
    avg_benzin = cph_avg(items, "95")
    avg_diesel = cph_avg(items, "diesel")
    cph_count  = sum(1 for s in items if CPH_MIN <= int(s.get("postal_code") or 0) <= CPH_MAX)

    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    except Exception:
        history = []

    new_entry = {
        "timestamp":    data["fetched_at"],
        "benzin":       avg_benzin,
        "diesel":       avg_diesel,
        "stationCount": cph_count,
    }

    # Only append when prices actually changed
    last = history[-1] if history else {}
    if last.get("benzin") != avg_benzin or last.get("diesel") != avg_diesel:
        history.append(new_entry)
        print(f"New history entry: benzin={avg_benzin}, diesel={avg_diesel} ({cph_count} stations)")
    else:
        print("Prices unchanged — no new history entry added.")

    history = history[-MAX_HISTORY:]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, separators=(",", ":"))
    print(f"history.json updated ({len(history)} entries)")


if __name__ == "__main__":
    main()
