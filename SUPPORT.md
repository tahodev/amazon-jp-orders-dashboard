# サポート

## 最初に確認すること

1. Windowsで`start_dashboard.bat`を実行します。
2. 黒いウィンドウに`[OK] 起動前チェック完了`が表示されることを確認します。
3. Chrome拡張機能の表示が`ローカル受信サービス：接続済み`になっているか確認します。
4. ソースを更新した場合は、`chrome://extensions/`で拡張機能を再読み込みします。

詳しい手順は[インストールガイド](docs/INSTALL.md)を参照してください。

## 不具合を報告する

[Bug report](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/issues/new?template=bug_report.yml)を利用してください。
Amazonの画面構造変更に関する報告では、ChromeとPythonのバージョン、発生した画面、再現手順が役立ちます。

次の情報は絶対に添付しないでください。

- 実在する注文番号、商品履歴、氏名、住所、支払情報
- Amazonアカウント画面のスクリーンショット
- `data/`配下のDB、CSV、JSON、HTML
- Cookie、トークン、パスワード、OTP

例が必要な場合は`503-0000000-0000001`のような合成注文番号を使用してください。

## セキュリティ問題

公開Issueには書かず、GitHubのPrivate vulnerability reportingを利用してください。詳細は[SECURITY.md](SECURITY.md)にあります。

## 対応範囲

このプロジェクトは個人メンテナンスのOSSです。最新リリースを優先して対応しますが、回答時間やAmazon側の仕様変更への追随は保証できません。
