# Amazon JP Orders Dashboard

**Turn your signed-in Amazon.co.jp order history into a private, local spending dashboard.**

One-click incremental sync, item-level expense categories, monthly charts, and
CSV export. No cloud account, no Amazon credentials, no telemetry.

> 日本語: Amazon.co.jp の注文履歴を、ログイン済み Chrome からローカルに取り込み、月別・カテゴリ別に可視化します。
>
> 中文：使用已登录 Chrome，把日本亚马逊订单历史保存到本地并生成支出统计面板。

![Sanitized dashboard preview](docs/assets/dashboard-demo.png)

## Why this project

Amazon's order page is useful for finding an order, but awkward for answering:

- How much did I spend each month?
- What did I spend on food, children, beauty, or daily necessities?
- Which multi-item orders account for the total?
- What changed since my last export?

This project keeps the workflow inspectable: a Chrome extension reads only the
pages you ask it to read, a Python receiver stores the result in local SQLite,
and a static dashboard presents the totals.

## Highlights

- **One-click latest sync**: resumes near the newest local order and overlaps 14 days to refresh recent changes.
- **Real item details**: opens order-detail pages for multi-item orders instead of assigning the whole total to one title.
- **Local-first**: order data stays under `data/` on your computer.
- **No credentials**: reuses your existing signed-in Chrome session; passwords, OTPs, and cookies are never stored.
- **Useful outputs**: SQLite, UTF-8 CSV, JSON snapshots, and a local HTML dashboard.
- **Editable categories**: manual corrections are remembered for matching product titles.
- **Auditable automation**: visible progress, deliberately slow page navigation, and no purchase/account actions.
- **Small stack**: Python standard library, vanilla JavaScript, SQLite, and a Manifest V3 extension.

## Quick start

Requirements: Windows, Python 3.10+, Google Chrome, and an Amazon.co.jp account
already signed in to Chrome.

1. Clone or download this repository.
2. Run:

   ```bat
   scripts\start_amazon_jp_orders.bat
   ```

3. Open `chrome://extensions/`, enable **Developer mode**, choose **Load unpacked**, and select `chrome_extension`.
4. Click the extension icon and choose **一键同步最新订单**.
5. Keep the Batch tab open. The dashboard opens automatically when the sync finishes.

After updating the source, restart the BAT receiver and click **Reload** for the
extension on `chrome://extensions/`.

### macOS / Linux receiver

The extension and Python service are platform-neutral; only the convenience BAT
file is Windows-specific.

```bash
python run.py serve --host 127.0.0.1 --port 8776
```

Then load `chrome_extension` as an unpacked extension.

## Sync modes

| Mode | Use it for | Behavior |
|---|---|---|
| One-click latest sync | Routine updates | Current year, latest local order minus 14 days through today |
| Date-range capture | Backfilling or repairing history | Selected year and explicit start/end dates |
| Current-page capture | Parser checks | Reads only the visible order-history page |

The overlap is intentional. Recent Amazon orders can change, and several orders
can share a date. SQLite upserts by order ID and item key, so overlap refreshes
records without double-counting spending.

## Data and privacy

Local files are written to:

```text
data/
├── amazon_jp_orders.db
├── dashboard.html
├── exports/
│   ├── orders.csv
│   └── order_items.csv
└── snapshots/
```

`data/` is ignored by Git. It still contains private purchase information, so
do not attach it to issues or publish it elsewhere. See [PRIVACY.md](PRIVACY.md)
and [SECURITY.md](SECURITY.md).

The receiver refuses non-loopback binding, rejects untrusted browser origins,
requires JSON for writes, and serves the dashboard with restrictive security
headers. The extension is limited to Amazon.co.jp and the local receiver.

## Categories

The default categories are:

- Food & drink / 食品饮料
- Children / 儿童
- Beauty & skincare / 美妆护肤
- Medicine & daily necessities / 药品日用品
- Other / 其他

Keyword rules live in `config/category_rules.json`. You can also change a
category directly in the item table; the local override is remembered for
identical titles.

## Architecture

```text
Signed-in Chrome
  └─ Manifest V3 extension (read-only Amazon pages)
       └─ JSON → http://127.0.0.1:8776
            └─ Python receiver
                 ├─ SQLite + snapshots + CSV
                 └─ local dashboard
```

The tool never clicks buy, cancel, return, exchange, payment, or account-setting
controls. Login challenges and CAPTCHA require manual handling.

## Development

```text
python -m pip install pytest
python -m pytest
node --check chrome_extension/popup.js
node --check chrome_extension/batch.js
node --check chrome_extension/capture_core.js
python scripts/check_public_release.py
```

The repository ships only synthetic fixtures. Contributions that change Amazon
DOM parsing should avoid real account screenshots and order IDs. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Limitations

- Amazon can change its page structure without notice.
- The current parser targets Amazon.co.jp's Japanese order-history experience.
- Item-level prices may be unavailable for some promotions, refunds, digital orders, or unusual fulfillment layouts.
- This is a personal spending aid, not accounting, tax, or financial advice.

## Related work

Earlier community tools demonstrated the demand for Amazon.co.jp history export,
including `kchgoh/amazon-japan-orderhist-download`,
`motemen/amazon-gather-order-history`, and yearly aggregation bookmarklets. This
project focuses on incremental local sync, item-level categorization, and a
persistent dashboard.

## License

MIT. This independent project is not affiliated with or endorsed by Amazon.
