from __future__ import annotations

import csv
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .classify import CATEGORIES, classify_title, load_rules
from .paths import AppPaths, ensure_dirs

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class IngestResult:
    saved_orders: int
    saved_items: int
    skipped_items: int


class OrdersDB:
    def __init__(self, paths: AppPaths):
        ensure_dirs(paths)
        self.paths = paths
        self.conn = sqlite3.connect(paths.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS capture_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                source_url TEXT NOT NULL,
                since_date TEXT NOT NULL,
                order_count INTEGER NOT NULL,
                item_count INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                order_total_yen INTEGER,
                detail_url TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                captured_at TEXT NOT NULL,
                raw_snapshot_path TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                title TEXT NOT NULL,
                item_url TEXT NOT NULL DEFAULT '',
                asin TEXT NOT NULL DEFAULT '',
                quantity INTEGER NOT NULL DEFAULT 1,
                item_price_yen INTEGER,
                item_total_yen INTEGER,
                category TEXT NOT NULL,
                category_source TEXT NOT NULL DEFAULT 'rule',
                matched_keyword TEXT NOT NULL DEFAULT '',
                seller TEXT NOT NULL DEFAULT '',
                captured_at TEXT NOT NULL,
                raw_snapshot_path TEXT NOT NULL DEFAULT '',
                UNIQUE(order_id, title, item_url)
            );
            CREATE TABLE IF NOT EXISTS category_overrides (
                pattern TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            );
            """
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.conn.commit()

    def ingest_capture(self, payload: dict[str, Any]) -> IngestResult:
        captured_now = datetime.now().astimezone()
        captured_at = captured_now.isoformat(timespec="seconds")
        source_url = str(payload.get("source_url") or payload.get("url") or "").strip()
        since_date = str(payload.get("since_date") or f"{captured_now.year}-01-01").strip()
        orders = payload.get("orders")
        if not isinstance(orders, list):
            raise TypeError("payload.orders must be a list")

        snapshot_path = self._save_snapshot(payload, captured_at)
        rules = load_rules(self.paths.category_rules_path)
        overrides = self._load_overrides()
        saved_orders = 0
        saved_items = 0
        skipped_items = 0

        with self.conn:
            for order in orders:
                if not isinstance(order, dict):
                    continue
                order_id = str(order.get("order_id") or "").strip()
                order_date = normalize_date(str(order.get("order_date") or ""))
                if not order_id or not order_date:
                    continue
                year, month = year_month(order_date)
                total_yen = parse_yen(order.get("order_total_yen") or order.get("order_total"))
                detail_url = str(order.get("detail_url") or "").strip()
                self.conn.execute(
                    """
                    INSERT INTO orders(
                        order_id, order_date, year, month, order_total_yen,
                        detail_url, source_url, captured_at, raw_snapshot_path
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_id) DO UPDATE SET
                        order_date=excluded.order_date,
                        year=excluded.year,
                        month=excluded.month,
                        order_total_yen=excluded.order_total_yen,
                        detail_url=excluded.detail_url,
                        source_url=excluded.source_url,
                        captured_at=excluded.captured_at,
                        raw_snapshot_path=excluded.raw_snapshot_path
                    """,
                    (
                        order_id,
                        order_date,
                        year,
                        month,
                        total_yen,
                        detail_url,
                        source_url,
                        captured_at,
                        str(snapshot_path),
                    ),
                )
                saved_orders += 1
                items = order.get("items")
                if not isinstance(items, list) or not items:
                    items = [
                        {
                            "title": order.get("title") or order.get("item_title") or "",
                            "item_url": order.get("item_url") or "",
                            "quantity": order.get("quantity") or 1,
                            "item_price_yen": total_yen,
                            "item_total_yen": total_yen,
                        }
                    ]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    title = clean_text(str(item.get("title") or item.get("item_title") or ""))
                    if not title:
                        skipped_items += 1
                        continue
                    item_url = str(item.get("item_url") or item.get("url") or "").strip()
                    quantity = safe_int(item.get("quantity"), default=1)
                    price_yen = parse_yen(item.get("item_price_yen") or item.get("item_price"))
                    item_total = parse_yen(item.get("item_total_yen") or item.get("item_total"))
                    if item_total is None and price_yen is not None:
                        item_total = price_yen * max(quantity, 1)
                    category_result = self._classify_with_overrides(title, overrides, rules)
                    self.conn.execute(
                        """
                        INSERT INTO order_items(
                            order_id, order_date, year, month, title, item_url, asin,
                            quantity, item_price_yen, item_total_yen, category,
                            category_source, matched_keyword, seller, captured_at, raw_snapshot_path
                        )
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(order_id, title, item_url) DO UPDATE SET
                            order_date=excluded.order_date,
                            year=excluded.year,
                            month=excluded.month,
                            quantity=excluded.quantity,
                            item_price_yen=excluded.item_price_yen,
                            item_total_yen=excluded.item_total_yen,
                            category=excluded.category,
                            category_source=excluded.category_source,
                            matched_keyword=excluded.matched_keyword,
                            seller=excluded.seller,
                            captured_at=excluded.captured_at,
                            raw_snapshot_path=excluded.raw_snapshot_path
                        """,
                        (
                            order_id,
                            order_date,
                            year,
                            month,
                            title,
                            item_url,
                            str(item.get("asin") or "").strip(),
                            quantity,
                            price_yen,
                            item_total,
                            category_result["category"],
                            category_result["source"],
                            category_result["matched_keyword"],
                            clean_text(str(item.get("seller") or "")),
                            captured_at,
                            str(snapshot_path),
                        ),
                    )
                    saved_items += 1
            self.conn.execute(
                """
                INSERT INTO capture_runs(captured_at, source_url, since_date, order_count, item_count, note)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    captured_at,
                    source_url,
                    since_date,
                    saved_orders,
                    saved_items,
                    str(payload.get("note") or "").strip(),
                ),
            )
        return IngestResult(saved_orders, saved_items, skipped_items)

    def _save_snapshot(self, payload: dict[str, Any], captured_at: str) -> Path:
        safe_stamp = re.sub(r"[^0-9T:-]", "", captured_at).replace(":", "")
        path = self.paths.snapshots_dir / f"capture_{safe_stamp}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _load_overrides(self) -> list[tuple[str, str]]:
        rows = self.conn.execute("SELECT pattern, category FROM category_overrides").fetchall()
        return [
            (str(row["pattern"]).strip().lower(), str(row["category"]).strip())
            for row in rows
            if str(row["category"]).strip() in CATEGORIES
        ]

    @staticmethod
    def _classify_with_overrides(
        title: str,
        overrides: list[tuple[str, str]],
        rules: dict[str, list[str]],
    ) -> dict[str, str]:
        lower = title.lower()
        for pattern, category in overrides:
            if pattern and pattern in lower:
                return {"category": category, "source": "override", "matched_keyword": pattern}
        result = classify_title(title, rules)
        return {
            "category": result.category,
            "source": result.source,
            "matched_keyword": result.matched_keyword,
        }

    def update_item_category(self, item_id: int, category: str, *, remember: bool = True) -> dict[str, Any]:
        if category not in CATEGORIES:
            raise ValueError(f"invalid category: {category}")
        row = self.conn.execute(
            "SELECT id, title FROM order_items WHERE id = ?",
            (item_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"item not found: {item_id}")
        title = clean_text(str(row["title"] or ""))
        if not title:
            raise ValueError("item title is empty")
        with self.conn:
            cur = self.conn.execute(
                """
                UPDATE order_items
                SET category = ?, category_source = ?, matched_keyword = ?
                WHERE title = ?
                """,
                (category, "manual", "manual:title", title),
            )
            affected = cur.rowcount
            if remember:
                self.conn.execute(
                    """
                    INSERT INTO category_overrides(pattern, category, note)
                    VALUES(?, ?, ?)
                    ON CONFLICT(pattern) DO UPDATE SET
                        category=excluded.category,
                        note=excluded.note
                    """,
                    (title.lower(), category, f"manual dashboard update item_id={item_id}"),
                )
        return {"item_id": item_id, "title": title, "category": category, "affected_rows": affected}

    def summary(self) -> dict[str, Any]:
        monthly = [dict(row) for row in self.conn.execute(
            """
            SELECT year, month, SUM(COALESCE(item_total_yen, 0)) AS total_yen, COUNT(*) AS item_count
            FROM order_items
            GROUP BY year, month
            ORDER BY year, month
            """
        )]
        category_monthly = [dict(row) for row in self.conn.execute(
            """
            SELECT year, month, category, SUM(COALESCE(item_total_yen, 0)) AS total_yen, COUNT(*) AS item_count
            FROM order_items
            GROUP BY year, month, category
            ORDER BY year, month, category
            """
        )]
        categories = [dict(row) for row in self.conn.execute(
            """
            SELECT category, SUM(COALESCE(item_total_yen, 0)) AS total_yen, COUNT(*) AS item_count
            FROM order_items
            GROUP BY category
            ORDER BY total_yen DESC
            """
        )]
        recent_items = [dict(row) for row in self.conn.execute(
            """
            SELECT id, year, month, order_date, order_id, title, item_url, quantity, item_total_yen, category, matched_keyword
            FROM order_items
            ORDER BY order_date DESC, id DESC
            LIMIT 300
            """
        )]
        runs = [dict(row) for row in self.conn.execute(
            """
            SELECT captured_at, source_url, since_date, order_count, item_count, note
            FROM capture_runs
            ORDER BY id DESC
            LIMIT 20
            """
        )]
        return {
            "monthly": monthly,
            "category_monthly": category_monthly,
            "categories": categories,
            "recent_items": recent_items,
            "runs": runs,
        }

    def sync_state(self, year: int) -> dict[str, Any]:
        order_row = self.conn.execute(
            """
            SELECT MAX(order_date) AS latest_order_date, COUNT(*) AS order_count
            FROM orders
            WHERE year = ?
            """,
            (year,),
        ).fetchone()
        run_row = self.conn.execute(
            "SELECT MAX(captured_at) AS last_captured_at FROM capture_runs"
        ).fetchone()
        return {
            "year": year,
            "latest_order_date": str(order_row["latest_order_date"] or ""),
            "order_count": int(order_row["order_count"] or 0),
            "last_captured_at": str(run_row["last_captured_at"] or ""),
        }

    def export_csv(self) -> dict[str, Path]:
        self.paths.exports_dir.mkdir(parents=True, exist_ok=True)
        orders_path = self.paths.exports_dir / "orders.csv"
        items_path = self.paths.exports_dir / "order_items.csv"
        self._write_query_csv(
            orders_path,
            "SELECT * FROM orders ORDER BY order_date DESC, order_id DESC",
        )
        self._write_query_csv(
            items_path,
            "SELECT * FROM order_items ORDER BY order_date DESC, order_id DESC, id DESC",
        )
        return {"orders": orders_path, "items": items_path}

    def _write_query_csv(self, path: Path, query: str) -> None:
        rows = self.conn.execute(query).fetchall()
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            if not rows:
                f.write("")
                return
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))


def normalize_date(value: str) -> str:
    text = clean_text(value)
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def year_month(date_text: str) -> tuple[int, int]:
    m = re.match(r"(\d{4})-(\d{2})-\d{2}", date_text)
    if not m:
        raise ValueError(f"invalid date: {date_text}")
    return int(m.group(1)), int(m.group(2))


def parse_yen(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value)
    text = str(value)
    if not text.strip():
        return None
    negative = "−" in text or "-" in text
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return None
    amount = int(digits)
    return -amount if negative else amount


def safe_int(value: Any, *, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u3000", " ")).strip()
