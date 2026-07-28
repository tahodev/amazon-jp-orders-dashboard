from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "run.py",
    "amazon_jp_orders/server.py",
    "chrome_extension/manifest.json",
    "config/category_rules.json",
)


def main() -> int:
    errors: list[str] = []
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    if sys.version_info < (3, 10):
        errors.append("Python 3.10 以降が必要です。")

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"必要なファイルがありません: {relative}")

    try:
        rules = json.loads((ROOT / "config" / "category_rules.json").read_text(encoding="utf-8"))
        categories = [name for name, keywords in rules.items() if isinstance(name, str) and isinstance(keywords, list)]
        if not categories:
            errors.append("カテゴリ設定を読み込めません。")
        else:
            print(f"[OK] カテゴリ設定: {len(categories)}分類 + その他")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"カテゴリ設定が壊れています: {exc}")

    data_dir = ROOT / "data"
    try:
        data_dir.mkdir(exist_ok=True)
        probe = data_dir / ".write-test"
        probe.write_text("ok", encoding="ascii")
        probe.unlink()
        print("[OK] ローカルデータ保存先に書き込めます")
    except OSError as exc:
        errors.append(f"dataフォルダに書き込めません: {exc}")

    try:
        with urllib.request.urlopen("http://127.0.0.1:8776/api/health", timeout=0.4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("ok") is True and payload.get("service") == "amazon-jp-orders":
            print("[情報] 受信サービスはすでに起動しています")
    except (OSError, ValueError, urllib.error.URLError):
        print("[OK] 新しい受信サービスを起動できます")

    if errors:
        for error in errors:
            print(f"[エラー] {error}")
        return 1
    print("[OK] 起動前チェック完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
