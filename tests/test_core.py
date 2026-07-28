import json
from pathlib import Path
from tempfile import TemporaryDirectory

from amazon_jp_orders.classify import classify_title, load_rules
from amazon_jp_orders.dashboard import render_dashboard
from amazon_jp_orders.db import OrdersDB, normalize_date, parse_yen
from amazon_jp_orders.paths import get_paths
from amazon_jp_orders.server import _host_allowed, _origin_allowed


ROOT = Path(__file__).resolve().parents[1]


def test_parse_yen():
    assert parse_yen("￥4,911") == 4911
    assert parse_yen("¥ 9,602") == 9602
    assert parse_yen("-￥179") == -179


def test_normalize_date():
    assert normalize_date("注文日 2026年6月8日") == "2026-06-08"
    assert normalize_date("2026/1/2") == "2026-01-02"


def test_classify_examples():
    rules = load_rules(get_paths().category_rules_path)
    assert classify_title("令和7年産 玄米 2kg ヒノヒカリ", rules).category == "食品・飲料"
    assert classify_title("マミーポコ パンツ サンリオキャラクターズデザイン オムツ", rules).category == "子ども用品"
    assert classify_title("すっぴんクリームC パステルローズの香り30g", rules).category == "美容・スキンケア"
    assert classify_title("オカモト コンドームズ ピュアマーガレット 12個入", rules).category == "医薬品・日用品"


def test_sync_state():
    with TemporaryDirectory() as temp_dir:
        db = OrdersDB(get_paths(Path(temp_dir)))
        try:
            with db.conn:
                db.conn.execute(
                    """
                    INSERT INTO orders(order_id, order_date, year, month, order_total_yen, captured_at)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    ("503-test", "2026-07-20", 2026, 7, 1200, "2026-07-21T08:00:00"),
                )
                db.conn.execute(
                    """
                    INSERT INTO capture_runs(captured_at, source_url, since_date, order_count, item_count, note)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    ("2026-07-21T08:00:00", "test", "2026-07-01", 1, 1, "test"),
                )
            assert db.sync_state(2026) == {
                "year": 2026,
                "latest_order_date": "2026-07-20",
                "order_count": 1,
                "last_captured_at": "2026-07-21T08:00:00",
            }
            assert db.sync_state(2025)["latest_order_date"] == ""
        finally:
            db.close()


def test_local_request_boundaries():
    assert _host_allowed("127.0.0.1:8776", 8776)
    assert _host_allowed("localhost:8776", 8776)
    assert not _host_allowed("attacker.example:8776", 8776)
    assert _origin_allowed("http://127.0.0.1:8776", 8776)
    assert _origin_allowed("chrome-extension://abcdefghijklmnopabcdefghijklmnop", 8776)
    assert not _origin_allowed("https://attacker.example", 8776)


def test_dashboard_hides_local_paths_and_escapes_script_content():
    data = {
        "monthly": [{"year": 2026, "month": 1, "total_yen": 100, "item_count": 1}],
        "category_monthly": [
            {"year": 2026, "month": 1, "category": "その他", "total_yen": 100, "item_count": 1}
        ],
        "categories": [{"category": "その他", "total_yen": 100, "item_count": 1}],
        "recent_items": [
            {
                "id": 1,
                "year": 2026,
                "month": 1,
                "order_date": "2026-01-01",
                "order_id": "503-0000000-0000001",
                "title": "</script><script>alert('x')</script>",
                "quantity": 1,
                "item_total_yen": 100,
                "category": "その他",
                "matched_keyword": "",
            }
        ],
        "runs": [],
    }
    with TemporaryDirectory() as temp_dir:
        private_root = Path(temp_dir) / "private-user-path"
        output = render_dashboard(
            data,
            {
                "orders": private_root / "orders.csv",
                "items": private_root / "order_items.csv",
            },
        )
    assert str(private_root) not in output
    assert "</script><script>alert" not in output
    assert "&lt;/script&gt;&lt;script&gt;" in output


def test_public_versions_match():
    manifest = json.loads((ROOT / "chrome_extension" / "manifest.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{manifest["version"]}"' in pyproject
