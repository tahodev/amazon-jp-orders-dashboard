from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .dashboard import build_dashboard
from .db import OrdersDB
from .paths import get_paths

MAX_BODY_BYTES = 25 * 1024 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}


def run_server(host: str = "127.0.0.1", port: int = 8776) -> None:
    if host.lower() not in LOOPBACK_HOSTS:
        raise ValueError("receiver must bind to 127.0.0.1 or localhost")
    paths = get_paths()
    db = OrdersDB(paths)
    build_dashboard(db)

    class Handler(BaseHTTPRequestHandler):
        server_version = "AmazonJPOrdersReceiver/0.1"

        def do_OPTIONS(self) -> None:
            if not self._validate_browser_request():
                return
            self._send_json(204, {})

        def do_GET(self) -> None:
            if not self._validate_browser_request():
                return
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/dashboard"}:
                self._send_file(paths.dashboard_path, "text/html; charset=utf-8")
                return
            if parsed.path == "/api/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "service": "amazon-jp-orders",
                        "db_path": str(paths.db_path),
                        "dashboard_path": str(paths.dashboard_path),
                    },
                )
                return
            if parsed.path == "/api/summary":
                self._send_json(200, {"ok": True, "data": db.summary()})
                return
            if parsed.path == "/api/sync-state":
                query = parse_qs(parsed.query)
                year = _safe_int((query.get("year") or [""])[0], default=0)
                if year < 2010 or year > 9999:
                    self._send_json(400, {"ok": False, "error": "invalid year"})
                    return
                self._send_json(200, {"ok": True, **db.sync_state(year)})
                return
            self._send_json(404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            if not self._validate_browser_request():
                return
            parsed = urlparse(self.path)
            if parsed.path == "/api/capture":
                self._handle_capture()
                return
            if parsed.path == "/api/item-category":
                self._handle_item_category()
                return
            self._send_json(404, {"ok": False, "error": "not found"})

        def _read_json_body(self) -> dict[str, Any] | None:
            content_type = str(self.headers.get("Content-Type") or "").lower()
            if not content_type.startswith("application/json"):
                self._send_json(415, {"ok": False, "error": "Content-Type must be application/json"})
                return None
            length = _safe_int(self.headers.get("Content-Length"), default=0)
            if length <= 0:
                self._send_json(400, {"ok": False, "error": "empty request body"})
                return None
            if length > MAX_BODY_BYTES:
                self._send_json(413, {"ok": False, "error": "payload too large"})
                return None
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._send_json(400, {"ok": False, "error": f"invalid json: {exc}"})
                return None
            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "JSON body must be an object"})
                return None
            return payload

        def _validate_browser_request(self) -> bool:
            if not _host_allowed(str(self.headers.get("Host") or ""), port):
                self._send_json(421, {"ok": False, "error": "invalid host"})
                return False
            origin = str(self.headers.get("Origin") or "").strip()
            if origin and not _origin_allowed(origin, port):
                self._send_json(403, {"ok": False, "error": "origin not allowed"})
                return False
            return True

        def _handle_capture(self) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            try:
                result = db.ingest_capture(payload)
                dashboard_path = build_dashboard(db)
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "saved_orders": result.saved_orders,
                        "saved_items": result.saved_items,
                        "skipped_items": result.skipped_items,
                        "dashboard_url": f"http://{host}:{port}/dashboard",
                        "dashboard_path": str(dashboard_path),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - HTTP boundary must return JSON instead of crashing
                self._send_json(500, {"ok": False, "error": str(exc)})

        def _handle_item_category(self) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            try:
                item_id = _safe_int(str(payload.get("item_id") or ""), default=0)
                category = str(payload.get("category") or "").strip()
                remember = bool(payload.get("remember", True))
                result = db.update_item_category(item_id, category, remember=remember)
                dashboard_path = build_dashboard(db)
                self._send_json(
                    200,
                    {
                        "ok": True,
                        **result,
                        "dashboard_url": f"http://{host}:{port}/dashboard",
                        "dashboard_path": str(dashboard_path),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - HTTP boundary must return JSON instead of crashing
                self._send_json(500, {"ok": False, "error": str(exc)})

        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"[amazon_jp_orders] {self.address_string()} {fmt % args}")

        def _send_json(self, status: int, data: dict[str, Any]) -> None:
            body = b"" if status == 204 else json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self._send_security_headers()
            origin = str(self.headers.get("Origin") or "").strip()
            if origin and _origin_allowed(origin, port):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Vary", "Origin")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    pass

        def _send_file(self, path: Path, content_type: str) -> None:
            if not path.exists():
                self._send_json(404, {"ok": False, "error": "file not found"})
                return
            body = path.read_bytes()
            self.send_response(200)
            self._send_security_headers()
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                pass

        def _send_security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                "connect-src 'self'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            )

    httpd = HTTPServer((host, port), Handler)
    print(f"[amazon_jp_orders] receiver listening on http://{host}:{port}")
    print(f"[amazon_jp_orders] dashboard: http://{host}:{port}/dashboard")
    print(f"[amazon_jp_orders] load extension from: {paths.root / 'chrome_extension'}")
    try:
        httpd.serve_forever()
    finally:
        db.close()
        httpd.server_close()


def _safe_int(value: str | None, *, default: int) -> int:
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return default


def _host_allowed(host_header: str, port: int) -> bool:
    return host_header.strip().lower() in {f"127.0.0.1:{port}", f"localhost:{port}"}


def _origin_allowed(origin: str, port: int) -> bool:
    normalized = origin.strip().lower().rstrip("/")
    if normalized in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
        return True
    return re.fullmatch(r"chrome-extension://[a-p]{32}", normalized) is not None
