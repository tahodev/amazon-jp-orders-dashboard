from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    data_dir: Path
    config_dir: Path
    db_path: Path
    exports_dir: Path
    snapshots_dir: Path
    dashboard_path: Path
    category_rules_path: Path


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_paths(root: Path | None = None) -> AppPaths:
    base = root or module_root()
    data_dir = base / "data"
    return AppPaths(
        root=base,
        data_dir=data_dir,
        config_dir=base / "config",
        db_path=data_dir / "amazon_jp_orders.db",
        exports_dir=data_dir / "exports",
        snapshots_dir=data_dir / "snapshots",
        dashboard_path=data_dir / "dashboard.html",
        category_rules_path=base / "config" / "category_rules.json",
    )


def ensure_dirs(paths: AppPaths) -> None:
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.exports_dir.mkdir(parents=True, exist_ok=True)
    paths.snapshots_dir.mkdir(parents=True, exist_ok=True)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
