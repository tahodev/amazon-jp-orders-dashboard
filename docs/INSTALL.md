# インストールガイド

## 必要環境

- Windows 10/11
- Python 3.10以降
- Google Chrome
- Amazon.co.jpにログイン済みのChromeプロフィール

Amazonのパスワード、OTP、Cookieをこのツールへ入力する必要はありません。

## 1. ダウンロード

[Releases](https://github.com/HanaCROOK/amazon-jp-orders-dashboard/releases/latest)から
`amazon-jp-orders-dashboard-vX.Y.Z.zip`をダウンロードし、任意の場所へ展開します。

`Source code (zip)`ではなく、Assets欄の上記ZIPを推奨します。ファイルの改ざんを確認したい場合は、同梱の`.sha256`と比較してください。

```powershell
Get-FileHash .\amazon-jp-orders-dashboard-vX.Y.Z.zip -Algorithm SHA256
```

## 2. ローカルサービスを起動

展開したフォルダの`start_dashboard.bat`をダブルクリックします。初回はPythonと必要ファイル、カテゴリ設定、保存先を自動確認します。

正常な場合は次の表示になります。

```text
[OK] Python 3.x.x
[OK] カテゴリ設定: 5分類
[OK] ローカルデータ保存先に書き込めます
[OK] 起動前チェック完了
```

支出ダッシュボードが開きます。注文を同期するときは黒いウィンドウを開いたままにします。

## 3. Chrome拡張機能を読み込む

1. Chromeで`chrome://extensions/`を開きます。
2. 右上の**デベロッパーモード**を有効にします。
3. **パッケージ化されていない拡張機能を読み込む**を選びます。
4. 展開したフォルダ内の`chrome_extension`を指定します。
5. ツールバーの拡張機能一覧からAmazon JP Ordersを固定します。

拡張機能に`ローカル受信サービス：接続済み`と表示されれば準備完了です。

## 4. 最初の同期

1. 拡張機能を開き、**最新の注文を同期**を押します。
2. 必要に応じてAmazonへログインします。
3. 同期専用タブを完了まで開いたままにします。
4. 完了後に開く支出ダッシュボードで内容を確認します。

過去年度は年・開始日・終了日を指定して**指定期間を取り込む**を使用します。

## 更新

新しいRelease ZIPを別フォルダへ展開し、古いフォルダの`data`を新しいフォルダへコピーします。その後、Chromeの拡張機能パスを新しい`chrome_extension`へ変更してください。

コピー前に黒い受信サービス画面を閉じてください。`data`には個人の購入履歴が含まれるため、クラウドやGitHubへ公開しないでください。

## アンインストール

Chromeの拡張機能を削除し、展開したフォルダを削除します。注文履歴も消す場合は、削除前に`data`フォルダが不要であることを確認してください。

## トラブルシューティング

- **Pythonが見つからない**: Python 3.10以降をインストールし、インストーラーの`Add Python to PATH`を有効にします。
- **受信サービスが停止中**: `start_dashboard.bat`を起動し、黒い画面を閉じないでください。
- **ポート8776を使用中**: 既に起動しているAmazon JP Ordersの画面がないか確認します。
- **同期が進まない**: Amazonのログイン確認やCAPTCHAが表示されていないか確認します。
- **更新後に動かない**: `chrome://extensions/`で拡張機能を再読み込みします。

解決しない場合は[SUPPORT.md](../SUPPORT.md)を確認してください。
