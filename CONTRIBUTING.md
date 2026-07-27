# Contributing

Thanks for helping improve Amazon JP Orders Dashboard.

## Before opening a pull request

1. Never commit real order history, screenshots, cookies, account names, addresses, or payment data.
2. Use synthetic order IDs such as `503-0000000-0000001` in fixtures.
3. Keep Amazon access read-only. Do not add purchase, cancellation, return, payment, or account-modification actions.
4. Keep dependencies minimal and explain any new Chrome permission.
5. Run:

   ```text
   python -m pytest -q
   node --check chrome_extension/popup.js
   node --check chrome_extension/batch.js
   node --check chrome_extension/capture_core.js
   python scripts/check_public_release.py
   ```

Amazon changes its markup regularly. DOM parser changes should include a
sanitized fixture or a clear description of the observed page structure.
