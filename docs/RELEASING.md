# Release procedure

1. Keep `pyproject.toml` and `chrome_extension/manifest.json` versions identical.
2. Update `CHANGELOG.md`.
3. Run the full verification suite.
4. Build deterministic assets:

   ```text
   python scripts/build_release.py
   ```

5. Upload both files under `dist/` to the matching GitHub Release.

The build runs the public-data safety scanner before creating an archive. The
ZIP contains runtime files, the sanitized dashboard preview, and user
documentation only. Repository automation, maintainer scripts, tests, caches,
social-preview sources, and local `data/` are excluded.
