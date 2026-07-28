from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from amazon_jp_orders.dashboard import build_dashboard
from amazon_jp_orders.db import OrdersDB
from amazon_jp_orders.paths import get_paths
from amazon_jp_orders.server import run_server


def main() -> int:
    parser = argparse.ArgumentParser(description="Amazon.co.jp local order capture")
    sub = parser.add_subparsers(dest="cmd")

    serve = sub.add_parser("serve", help="Start local capture receiver")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8776)
    serve.add_argument("--open-browser", action="store_true", help="Open the dashboard after the receiver starts")

    sub.add_parser("dashboard", help="Rebuild dashboard and CSV exports")

    ingest = sub.add_parser("ingest", help="Ingest a JSON capture file")
    ingest.add_argument("json_file", help="Capture payload JSON path")

    args = parser.parse_args()
    if args.cmd in {None, "serve"}:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8776)
        dashboard_url = f"http://{host}:{port}/dashboard"
        if _receiver_ready(host, port):
            print(f"[amazon_jp_orders] receiver is already running on http://{host}:{port}")
            if getattr(args, "open_browser", False):
                webbrowser.open(dashboard_url)
            return 0
        on_ready = (lambda: webbrowser.open(dashboard_url)) if getattr(args, "open_browser", False) else None
        run_server(host=host, port=port, on_ready=on_ready)
        return 0

    paths = get_paths()
    db = OrdersDB(paths)
    try:
        if args.cmd == "dashboard":
            dashboard = build_dashboard(db)
            print(f"dashboard: {dashboard}")
            webbrowser.open(dashboard.resolve().as_uri())
            return 0
        if args.cmd == "ingest":
            payload = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
            result = db.ingest_capture(payload)
            dashboard = build_dashboard(db)
            print(f"saved_orders={result.saved_orders} saved_items={result.saved_items} skipped_items={result.skipped_items}")
            print(f"dashboard: {dashboard}")
            return 0
    finally:
        db.close()
    parser.error(f"unknown command: {args.cmd}")
    return 2


def _receiver_ready(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=0.4) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status == 200 and payload.get("ok") is True and payload.get("service") == "amazon-jp-orders"
    except (OSError, ValueError, urllib.error.URLError):
        return False


if __name__ == "__main__":
    raise SystemExit(main())
