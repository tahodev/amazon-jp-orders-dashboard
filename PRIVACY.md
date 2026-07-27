# Privacy Policy

Last updated: 2026-07-27

## Summary

Amazon JP Orders Dashboard is local-only software. It has no cloud service,
account system, telemetry, advertising, or analytics. The maintainers cannot
see your Amazon account or order history.

## Data processed locally

When you explicitly start a capture, the Chrome extension reads these fields
from your signed-in Amazon.co.jp order-history pages:

- order ID and order date;
- product title, product URL, ASIN, seller, price, and quantity when available;
- order total and order-detail URL.

It does not read or store your Amazon password, OTP, full payment-card number,
Chrome cookies, or browser profile files.

## Local storage

Order data is sent only to `http://127.0.0.1:8776` and stored under the local
`data/` directory as SQLite, JSON snapshots, CSV exports, and the generated
dashboard. That directory is excluded from Git.

Snapshots and exports still contain private purchase information. Do not post
them in issues, commits, screenshots, or bug reports.

## Network access

The extension accesses only:

- `https://www.amazon.co.jp/*` to read pages in your existing signed-in session;
- `http://127.0.0.1:8776/*` and `http://localhost:8776/*` for the local receiver.

No order data is sent to the project maintainers or a third-party service.

## Deleting data

Close the receiver, then run `scripts/reset_local_data.bat`, or manually remove
the local `data/` directory.

## Disclaimer

This independent project is not affiliated with, endorsed by, or sponsored by
Amazon. Amazon and related marks belong to their respective owners.
