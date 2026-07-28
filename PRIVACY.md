# プライバシーポリシー / Privacy Policy

最終更新日 / Last updated: 2026-07-28

## 日本語

### 概要

Amazon JP Orders Dashboardはローカル専用のソフトウェアです。クラウドサービス、独自アカウント、テレメトリー、広告、アクセス解析はありません。開発者や第三者が利用者のAmazonアカウントや注文履歴を受け取ることはありません。

### 読み取るデータ

利用者が拡張機能の取込ボタンを押したときだけ、ログイン済みのAmazon.co.jp注文履歴ページから次の情報を読み取ります。

- 注文番号、注文日、注文合計、注文内容ページのURL
- 商品名、商品URL、ASIN、販売者、価格、数量（ページに表示される場合）

Amazonのパスワード、ワンタイムパスワード、Cookie、Chromeプロフィール、カード番号、請求先住所は読み取りも保存もしません。

### 利用目的と保存先

読み取ったデータは、月別・カテゴリ別の支出集計、商品明細、CSV出力を作成するためだけに使用します。データは`http://127.0.0.1:8776`のローカル受信サービスへ送られ、利用者のPCにある`data/`フォルダへSQLite、JSON、CSV、HTMLとして保存されます。

### 外部送信と第三者提供

注文データを開発者、広告事業者、分析事業者、その他の第三者へ販売、共有、転送しません。パーソナライズ広告、信用評価、プロファイリングには使用しません。開発者が注文データを閲覧することもありません。

拡張機能が通信する宛先は次の2つだけです。

- `https://www.amazon.co.jp/*`：利用者が明示的に開始した注文履歴の読取
- `http://127.0.0.1:8776/*`：同じPC上のローカル受信サービス

リモートコードの取得や実行は行いません。

### Chrome Web Store Limited Use

本拡張機能によるユーザーデータの利用は、画面で説明した単一目的である注文支出のローカル集計に限定されます。Chrome Web Store User Data Policy（Limited Use要件を含む）に準拠します。

### 保持期間と削除

データは利用者が削除するまでPC内に残ります。受信サービスを閉じて`scripts/reset_local_data.bat`を実行するか、`data/`フォルダを削除すると消去できます。拡張機能をChromeから削除しても、PC内の`data/`は自動では削除されません。

### 問い合わせ

個人情報を含めずに[GitHub Issues](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/issues)を利用してください。セキュリティ問題は[Private vulnerability reporting](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/security/advisories/new)へ報告してください。

---

## English

### Summary

Amazon JP Orders Dashboard is local-only software. It has no cloud service, account system, telemetry, advertising, or analytics. The maintainers and third parties cannot see your Amazon account or order history.

### Data processed

Only after the user explicitly starts a capture, the Chrome extension reads the following fields from signed-in Amazon.co.jp order-history pages:

- order ID, order date, order total, and order-detail URL;
- product title, product URL, ASIN, seller, price, and quantity when displayed.

It does not read or store Amazon passwords, OTPs, cookies, Chrome profiles, full payment-card numbers, or billing addresses.

### Purpose and local storage

The data is used only to produce monthly and category spending summaries, item details, and CSV exports. It is sent to the local receiver at `http://127.0.0.1:8776` and stored under the user's local `data/` directory as SQLite, JSON, CSV, and HTML.

### No external transfer

Order data is never sold, shared, or transferred to the maintainers, advertisers, analytics providers, or other third parties. It is not used for personalized advertising, credit decisions, or profiling, and no project maintainer has human access to it.

The extension communicates only with:

- `https://www.amazon.co.jp/*` to read order pages after a user action;
- `http://127.0.0.1:8776/*` to reach the local receiver on the same computer.

The extension does not download or execute remote code.

### Chrome Web Store Limited Use

Use of user data is limited to the extension's disclosed single purpose: creating a local spending summary from the user's order history. The extension complies with the Chrome Web Store User Data Policy, including the Limited Use requirements.

### Retention and deletion

Data remains on the user's computer until the user deletes it. Close the receiver and run `scripts/reset_local_data.bat`, or delete the local `data/` directory. Removing the Chrome extension does not automatically remove local files created by the companion service.

### Contact

Use [GitHub Issues](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/issues) without including personal data. Report security issues through [private vulnerability reporting](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/security/advisories/new).
