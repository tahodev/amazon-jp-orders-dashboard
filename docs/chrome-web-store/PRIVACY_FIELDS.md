# Chrome Web Store Privacy practices

The following text is prepared for the Developer Dashboard. Re-check the form labels at submission time because Google can revise them.

## Single purpose

ログイン済みのAmazon.co.jp注文履歴を利用者の操作で読み取り、同じPC上のローカル受信サービスへ保存して、月別・カテゴリ別の支出ダッシュボードとCSVを作成します。

English: Read signed-in Amazon.co.jp order-history pages after an explicit user action and save the results to a companion receiver on the same computer to create monthly, category, and CSV spending summaries.

## Permission justification

### `scripting`

利用者が取込ボタンを押したときに限り、対象のAmazon.co.jp注文履歴タブで同梱済みの解析関数を実行するために使用します。バックグラウンドで常時実行せず、リモートコードも実行しません。

Used only after a user presses a capture button to execute packaged parser functions in the relevant Amazon.co.jp order-history tab. It does not run continuously and does not execute remote code.

### `https://www.amazon.co.jp/*`

注文履歴一覧と、複数商品の価格を確認する注文内容ページを読み取るために必要です。購入、返品、支払方法、アカウント設定は操作しません。

Required to read order-history and order-detail pages, including item prices for multi-item orders. The extension does not buy, return, change payment methods, or modify account settings.

### `http://127.0.0.1:8776/*`

読み取った注文データを同じPC上のローカル受信サービスへ保存し、ローカルダッシュボードを開くために必要です。インターネット上のサーバーではありません。

Required to save captured data to the companion receiver and open the dashboard on the same computer. This is a loopback address, not an internet server.

## Remote code

Select **No**. All JavaScript executed by the extension is packaged in the submitted ZIP. No remote script, WebAssembly module, or remotely evaluated logic is downloaded.

## Data disclosures

Recommended selections:

- **Website content**: order IDs, dates, product titles, sellers, quantities, URLs, and ASINs shown on the pages.
- **Financial and payment information**: order totals and item prices. No payment-card or bank-account data is read.

Do not select authentication information, location, health, communications, general web history, or general user activity. The extension does not intentionally read names, addresses, passwords, OTPs, cookies, or card numbers.

## Data use certifications

Certify all Limited Use statements truthfully:

- data is used only for the disclosed local spending dashboard;
- data is not sold or transferred to third parties;
- data is not used for advertising, creditworthiness, or lending;
- maintainers do not have human access to user order data.

Privacy policy URL:

https://github.com/HanaCROOK/amazon-jp-orders-dashboard/blob/main/PRIVACY.md
