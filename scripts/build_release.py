from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
INCLUDED_ROOT_FILES = {
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "PRIVACY.md",
    "README.en.md",
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
    "SUPPORT.md",
    "pyproject.toml",
    "run.py",
    "start_dashboard.bat",
}
INCLUDED_DIRS = {"amazon_jp_orders", "chrome_extension", "config"}
INCLUDED_EXTRA_FILES = {
    "docs/INSTALL.md",
    "docs/assets/dashboard-demo.png",
    "scripts/doctor.py",
    "scripts/reset_local_data.bat",
    "scripts/start_amazon_jp_orders.bat",
}
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", "dist", "data"}


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("pyproject.toml に version がありません")
    return match.group(1)


def included_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS or part == ".git" for part in relative.parts):
            continue
        if len(relative.parts) == 1 and relative.name in INCLUDED_ROOT_FILES:
            files.append(path)
        elif relative.parts[0] in INCLUDED_DIRS:
            files.append(path)
        elif relative.as_posix() in INCLUDED_EXTRA_FILES:
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def run_safety_scan() -> None:
    subprocess.run([sys.executable, "scripts/check_public_release.py"], cwd=ROOT, check=True)


def build() -> tuple[Path, Path]:
    run_safety_scan()
    version = project_version()
    archive_root = f"amazon-jp-orders-dashboard-v{version}"
    DIST.mkdir(exist_ok=True)
    archive = DIST / f"{archive_root}.zip"
    checksum = archive.with_suffix(".zip.sha256")

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in included_files():
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{archive_root}/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            output.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"release: {archive}")
    print(f"sha256:  {digest}")
    return archive, checksum


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
