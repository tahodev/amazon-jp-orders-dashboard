from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "chrome_extension"
DIST = ROOT / "dist" / "chrome-web-store"
EXPECTED_PERMISSIONS = ["scripting"]
EXPECTED_HOSTS = ["https://www.amazon.co.jp/*", "http://127.0.0.1:8776/*"]
ICON_SIZES = {"16": 16, "32": 32, "48": 48, "128": 128}


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", header[16:24])


def validate_manifest() -> dict[str, object]:
    manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("manifest_version") != 3:
        errors.append("manifest_version must be 3")
    if manifest.get("permissions") != EXPECTED_PERMISSIONS:
        errors.append(f"permissions must be exactly {EXPECTED_PERMISSIONS}")
    if manifest.get("host_permissions") != EXPECTED_HOSTS:
        errors.append(f"host_permissions must be exactly {EXPECTED_HOSTS}")
    if len(str(manifest.get("description") or "")) > 132:
        errors.append("description exceeds 132 characters")
    icons = manifest.get("icons") or {}
    for key, expected_size in ICON_SIZES.items():
        relative = str(icons.get(key) or "") if isinstance(icons, dict) else ""
        path = EXTENSION / relative
        if not path.is_file():
            errors.append(f"missing {key}px icon: {relative}")
        elif png_size(path) != (expected_size, expected_size):
            errors.append(f"wrong icon dimensions: {relative} is {png_size(path)}")
    for path in EXTENSION.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        if re.search(r'<script[^>]+src=["\']https?://', text, flags=re.IGNORECASE):
            errors.append(f"remote script found: {path.name}")
    if errors:
        raise ValueError("\n".join(errors))
    return manifest


def extension_files() -> list[Path]:
    return sorted(
        (path for path in EXTENSION.rglob("*") if path.is_file() and "__pycache__" not in path.parts),
        key=lambda path: path.relative_to(EXTENSION).as_posix(),
    )


def build() -> tuple[Path, Path]:
    manifest = validate_manifest()
    version = str(manifest["version"])
    DIST.mkdir(parents=True, exist_ok=True)
    archive = DIST / f"amazon-jp-orders-extension-v{version}.zip"
    checksum = archive.with_suffix(".zip.sha256")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in extension_files():
            relative = path.relative_to(EXTENSION).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            output.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"web store package: {archive}")
    print(f"sha256: {digest}")
    return archive, checksum


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
