from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATEGORIES = ["食品饮料", "儿童", "美妆护肤", "药品日用品", "其他"]
CLASSIFY_ORDER = ["儿童", "食品饮料", "美妆护肤", "药品日用品"]


@dataclass(frozen=True)
class CategoryResult:
    category: str
    source: str
    matched_keyword: str = ""


DEFAULT_RULES: dict[str, list[str]] = {
    "食品饮料": [
        "食品",
        "飲料",
        "炭酸水",
        "天然水",
        "ミネラルウォーター",
        "お茶",
        "茶",
        "コーヒー",
        "ジュース",
        "米",
        "玄米",
        "ご飯",
        "パン",
        "菓子",
        "チョコ",
        "カレー",
        "ラーメン",
        "めん",
        "醤油",
        "味噌",
        "砂糖",
        "塩",
        "だし",
        "レトルト",
        "プロテイン",
    ],
    "儿童": [
        "ベビー",
        "赤ちゃん",
        "キッズ",
        "子供",
        "こども",
        "おむつ",
        "オムツ",
        "パンツ lサイズ",
        "パンツ mサイズ",
        "パンツ sサイズ",
        "マミーポコ",
        "ムーニー",
        "メリーズ",
        "おしりふき",
        "哺乳",
        "ミルク",
        "知育",
        "玩具",
    ],
    "美妆护肤": [
        "化粧",
        "コスメ",
        "美容",
        "スキンケア",
        "クリーム",
        "ローション",
        "乳液",
        "美容液",
        "クレンジング",
        "洗顔",
        "日焼け止め",
        "パステルローズ",
        "シャンプー",
        "トリートメント",
        "ヘアオイル",
    ],
    "药品日用品": [
        "医薬",
        "薬",
        "サプリ",
        "ビタミン",
        "マスク",
        "消毒",
        "湿布",
        "体温計",
        "洗剤",
        "柔軟剤",
        "掃除",
        "トイレット",
        "ティッシュ",
        "キッチンペーパー",
        "歯ブラシ",
        "歯磨き",
        "コンタクト",
        "コンドーム",
        "衛生",
        "ゴミ袋",
        "電池",
    ],
}


def load_rules(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        save_default_rules(path)
        return DEFAULT_RULES
    data = json.loads(path.read_text(encoding="utf-8"))
    rules: dict[str, list[str]] = {}
    for category in CATEGORIES:
        if category == "其他":
            continue
        values = data.get(category, DEFAULT_RULES.get(category, []))
        rules[category] = [str(item).strip() for item in values if str(item).strip()]
    return rules


def save_default_rules(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(DEFAULT_RULES, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def classify_title(title: str, rules: dict[str, list[str]]) -> CategoryResult:
    normalized = _normalize(title)
    if not normalized:
        return CategoryResult("其他", "rule", "")

    for category in CLASSIFY_ORDER:
        for keyword in rules.get(category, []):
            if _keyword_matches(normalized, keyword):
                return CategoryResult(category, "rule", keyword)
    return CategoryResult("其他", "rule", "")


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _keyword_matches(normalized_title: str, keyword: str) -> bool:
    key = _normalize(keyword)
    if not key:
        return False
    if re.search(r"[a-z0-9]", key):
        return key in normalized_title
    return key.lower() in normalized_title


def category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {category: 0 for category in CATEGORIES}
    for row in rows:
        category = str(row.get("category") or "其他")
        out[category if category in out else "其他"] += 1
    return out
