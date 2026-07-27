from __future__ import annotations

import argparse
import json
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

    sub.add_parser("dashboard", help="Rebuild dashboard and CSV exports")

    ingest = sub.add_parser("ingest", help="Ingest a JSON capture file")
    ingest.add_argument("json_file", help="Capture payload JSON path")

    args = parser.parse_args()
    if args.cmd in {None, "serve"}:
        run_server(host=getattr(args, "host", "127.0.0.1"), port=getattr(args, "port", 8776))
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


if __name__ == "__main__":
    raise SystemExit(main())
