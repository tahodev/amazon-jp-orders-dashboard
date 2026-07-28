# Amazon JP Orders Dashboard

[English](README.en.md)

[![CI](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/HanaCROOK/amazon-jp-orders-dashboard)](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-1f5e45.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg)](https://www.python.org/)

**ログイン済みのAmazon.co.jp注文履歴を、プライベートなローカル支出ダッシュボードに。**

最新注文のワンクリック同期、商品単位のカテゴリ分類、月別グラフ、CSV出力に対応します。
クラウドアカウント、Amazonの認証情報、テレメトリーは使用しません。

![匿名化されたダッシュボードのプレビュー](docs/assets/dashboard-demo.png)

> 注文履歴は外部サーバーへ送信されません。AmazonのパスワードやCookieも保存しません。

## 3ステップで始める

1. [最新Release](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/releases/latest)のZIPを展開します。
2. `start_dashboard.bat`をダブルクリックします。
3. Chromeで`chrome://extensions/`を開き、`chrome_extension`を読み込みます。

詳しい画面付き手順、更新、アンインストール、トラブル対応は[インストールガイド](docs/INSTALL.md)にまとめています。

## このプロジェクトについて

Amazonの注文履歴は注文を探すには便利ですが、次のような支出管理には向いていません。

- 月ごとの支出はいくらだったか
- 食品、子ども用品、美容、日用品などにいくら使ったか
- 複数商品を含む注文の内訳はどうなっているか
- 前回の取込後に何が増えたか

このツールでは、Chrome拡張機能が指定された注文履歴ページだけを読み取り、
Pythonのローカル受信サービスがSQLiteに保存し、ダッシュボードで集計結果を表示します。

## 主な機能

- **最新注文をワンクリック同期**：ローカルの最新注文から14日前まで遡り、最近の変更も更新します。
- **商品単位の明細**：複数商品を含む注文では注文内容ページを確認し、合計金額を1商品に誤配分しません。
- **ローカル保存**：注文データはパソコンの`data/`配下だけに保存されます。
- **認証情報を保存しない**：ログイン済みChromeを利用し、パスワード、OTP、Cookieを保存しません。
- **利用しやすい出力**：SQLite、UTF-8 CSV、JSONスナップショット、ローカルHTMLダッシュボード。
- **カテゴリ修正**：商品明細からカテゴリを変更でき、同じ商品名に対する修正を記憶します。
- **見える自動処理**：ページ移動と進捗を表示し、購入・返品・アカウント操作は行いません。
- **小さな構成**：Python標準ライブラリ、Vanilla JavaScript、SQLite、Manifest V3。

## クイックスタート（ソースから利用する場合）

必要環境：Windows、Python 3.10以降、Google Chrome、Chromeでログイン済みのAmazon.co.jpアカウント。

1. このリポジトリをクローンまたはダウンロードします。
2. 次のファイルを実行します。

   ```bat
   start_dashboard.bat
   ```

3. `chrome://extensions/`を開き、**デベロッパーモード**を有効にします。
4. **パッケージ化されていない拡張機能を読み込む**を選び、`chrome_extension`を指定します。
5. 拡張機能を開き、**最新の注文を同期**を押します。
6. 同期タブを開いたまま待ちます。完了すると支出ダッシュボードが自動的に開きます。

ソースを更新した場合は、BATの受信サービスを再起動し、
`chrome://extensions/`で拡張機能を再読み込みしてください。

### macOS / Linux

拡張機能とPythonサービスは各OSで利用できます。BATファイルだけがWindows専用です。

```bash
python run.py serve --host 127.0.0.1 --port 8776
```

その後、`chrome_extension`をパッケージ化されていない拡張機能として読み込みます。

## 同期モード

| モード | 用途 | 動作 |
|---|---|---|
| 最新の注文を同期 | 日常的な更新 | 今年の最新ローカル注文から14日前〜今日 |
| 指定期間を取り込む | 過去年度の補完・修復 | 選択した年と開始日・終了日 |
| 現在のページを取り込む | パーサー確認 | 表示中の注文履歴ページだけ |

14日間の重複読取は意図的なものです。最近の注文内容が更新された場合や、
同じ日に複数の注文がある場合も、注文番号と商品キーによるSQLiteの更新処理で
二重集計せずに最新状態へ更新します。

## データとプライバシー

ローカルファイルは次の場所に保存されます。

```text
data/
├── amazon_jp_orders.db
├── dashboard.html
├── exports/
│   ├── orders.csv
│   └── order_items.csv
└── snapshots/
```

`data/`はGitの対象外です。ただし購入履歴を含むため、Issue、コミット、
スクリーンショットなどで公開しないでください。詳細は[PRIVACY.md](PRIVACY.md)と
[SECURITY.md](SECURITY.md)を確認してください。

受信サービスはループバック以外の接続を拒否し、信頼できないブラウザOriginを遮断します。
書込APIはJSONのみを受け付け、ダッシュボードには制限の強いセキュリティヘッダーを付与します。
拡張機能の接続先はAmazon.co.jpとローカル受信サービスだけです。

### Chrome拡張機能の権限

| 権限 | 用途 |
|---|---|
| `scripting` | ボタン操作後に注文履歴ページで同梱パーサーを実行 |
| `https://www.amazon.co.jp/*` | 注文履歴と注文内容ページの読取 |
| `http://127.0.0.1:8776/*` | 同じPC上の受信サービスへの保存 |

`tabs`、Cookie、ダウンロード、支払、履歴全体、リモートコードの権限は使用しません。

## カテゴリ

初期カテゴリは次の5つです。

- 食品・飲料
- 子ども用品
- 美容・スキンケア
- 医薬品・日用品
- その他

キーワードルールは`config/category_rules.json`にあります。商品明細のカテゴリを
直接変更すると、同じ商品名に対するローカル修正として記憶されます。

## 構成

```text
ログイン済みChrome
  └─ Manifest V3拡張機能（Amazonページを読取専用で確認）
       └─ JSON → http://127.0.0.1:8776
            └─ Pythonローカル受信サービス
                 ├─ SQLite + スナップショット + CSV
                 └─ ローカルダッシュボード
```

購入、キャンセル、返品、交換、支払方法、アカウント設定の操作は行いません。
ログイン確認やCAPTCHAが表示された場合は、利用者が手動で対応する必要があります。

## 開発

```text
python -m pip install pytest
python -m pytest
node --check chrome_extension/popup.js
node --check chrome_extension/batch.js
node --check chrome_extension/capture_core.js
python scripts/check_public_release.py
python scripts/build_release.py
```

リポジトリには合成テストデータだけを収録しています。AmazonのDOM解析を変更するPRでは、
実在する注文番号、アカウント画面、個人情報を共有しないでください。
[CONTRIBUTING.md](CONTRIBUTING.md)も参照してください。

機能提案と不具合報告は[Issues](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/issues)、
今後の方向性は[ROADMAP.md](ROADMAP.md)、利用時の確認事項は[SUPPORT.md](SUPPORT.md)にあります。

## 制限事項

- Amazonのページ構造は予告なく変更される場合があります。
- 現在のパーサーはAmazon.co.jpの日本語版注文履歴を対象としています。
- 値引き、返金、デジタル商品、特殊な配送では商品単位の金額を取得できない場合があります。
- 個人の支出確認を補助するツールであり、会計・税務・金融上の助言ではありません。

## ライセンス

MIT License。このプロジェクトはAmazonとは関係なく、Amazonによる承認・支援を受けていません。
