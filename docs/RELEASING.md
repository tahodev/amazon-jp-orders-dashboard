# Release procedure

1. Keep `pyproject.toml` and `chrome_extension/manifest.json` versions identical.
2. Update `CHANGELOG.md`.
3. Run the full verification suite.
4. Build deterministic assets:

   ```text
   python scripts/build_release.py
   python scripts/build_webstore.py
   ```

5. Upload the runtime ZIP and checksum under `dist/` to the matching GitHub
   Release. The Chrome Web Store ZIP under `dist/chrome-web-store/` is the
   upload candidate for the Developer Dashboard.

The build runs the public-data safety scanner before creating an archive. The
ZIP contains runtime files, the sanitized dashboard preview, and user
documentation only. Repository automation, maintainer scripts, tests, caches,
social-preview sources, and local `data/` are excluded.

Store screenshots and icons are committed so contributors do not need the
maintainer-only rendering dependencies. To regenerate them, install Playwright
and Pillow, then run `python scripts/render_store_assets.py`.
