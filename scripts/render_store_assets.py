from __future__ import annotations

from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STORE_ASSETS = ROOT / "docs" / "chrome-web-store" / "assets"
ICON_DIR = ROOT / "chrome_extension" / "icons"


def render_page(page, source: Path, output: Path, width: int, height: int, *, transparent: bool = False) -> None:
    page.set_viewport_size({"width": width, "height": height})
    page.goto(source.resolve().as_uri(), wait_until="load")
    page.screenshot(path=str(output), omit_background=transparent)


def render_sync_screenshot(page, source: Path, output: Path) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(source.resolve().as_uri(), wait_until="load")
    frame = page.frame(name="popup")
    if frame is None:
        raise RuntimeError("popup preview frame was not loaded")
    frame.locator("#health").evaluate("element => element.textContent = 'ローカル受信サービス：接続済み'")
    frame.locator("#since").fill("2026-07-14")
    frame.locator("#until").fill("2026-07-28")
    frame.locator("#syncHint").evaluate(
        "element => element.textContent = '24件の注文を保存済み。最近の注文を自動更新します'"
    )
    frame.locator("body").evaluate("() => document.activeElement?.blur()")
    page.screenshot(path=str(output))


def main() -> int:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    STORE_ASSETS.mkdir(parents=True, exist_ok=True)
    icon_large = STORE_ASSETS / "icon-512.png"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 512, "height": 512})
        render_page(page, ROOT / "docs" / "brand" / "icon-source.svg", icon_large, 512, 512, transparent=True)
        render_page(page, STORE_ASSETS / "promo-small-source.html", STORE_ASSETS / "promo-small-440x280.png", 440, 280)
        render_sync_screenshot(
            page,
            STORE_ASSETS / "screenshot-sync-source.html",
            STORE_ASSETS / "screenshot-sync-1280x800.png",
        )
        browser.close()

    with Image.open(icon_large) as icon:
        for size in (16, 32, 48, 128):
            icon.resize((size, size), Image.Resampling.LANCZOS).save(ICON_DIR / f"icon{size}.png")
    with Image.open(ROOT / "docs" / "assets" / "dashboard-demo.png") as dashboard:
        dashboard.resize((1280, 800), Image.Resampling.LANCZOS).save(STORE_ASSETS / "screenshot-dashboard-1280x800.png")

    print(f"rendered extension icons: {ICON_DIR}")
    print(f"rendered store assets: {STORE_ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
