from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is required only to rebuild documentation images.")
        print("Install it with: python -m pip install playwright && playwright install chromium")
        return 1

    source = ROOT / "docs" / "assets" / "social-preview-source.html"
    output = ROOT / "docs" / "assets" / "social-preview.png"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 640}, device_scale_factor=1)
        page.goto(source.resolve().as_uri(), wait_until="load")
        page.screenshot(path=str(output))
        browser.close()
    print(f"rendered: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
