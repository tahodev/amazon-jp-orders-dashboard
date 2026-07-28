# Chrome Web Store review instructions

## Summary for the reviewer

This extension is a user-triggered, read-only parser for Amazon.co.jp order-history pages. It requires a companion Python receiver running only on `127.0.0.1:8776`. No test credentials are embedded or supplied.

## Setup

1. Download the latest runtime ZIP from:
   https://github.com/HanaCROOK/amazon-jp-orders-dashboard/releases/latest
2. Extract it on Windows with Python 3.10 or later installed.
3. Run `start_dashboard.bat` and keep its console window open.
4. Confirm that `http://127.0.0.1:8776/api/health` returns `{"ok": true, "service": "amazon-jp-orders"}`.
5. Install the submitted extension package.

## Functional test

1. Sign in to Amazon.co.jp using a reviewer-owned test account. The developer does not provide or request Amazon credentials.
2. Open the extension. It should display `ローカル受信サービス：接続済み`.
3. Open the account's order-history page.
4. Choose **現在のページを取り込む** to parse only the visible page, or **最新の注文を同期** to run the incremental flow.
5. Confirm that the local dashboard opens and that no request containing order data is sent to an internet host.

If the test account has no orders, the extension should complete with zero captured orders without modifying the Amazon account.

## Safety boundaries

- No purchase, cancellation, return, exchange, payment, or account-setting action exists.
- Parsing begins only after an explicit button click.
- Network destinations are limited by the manifest to Amazon.co.jp and the loopback receiver.
- All executable JavaScript is included in the ZIP; there is no remote code.
- Data is stored on the reviewer's own computer and can be deleted with `scripts/reset_local_data.bat`.
