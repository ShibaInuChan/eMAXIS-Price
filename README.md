# eMAXIS Slim 全世界株式（オール・カントリー）価格通知

毎平日の朝、eMAXIS Slim 全世界株式（オール・カントリー）の基準価額をLINEに自動送信するシステムです。

## 通知内容

📈 オルカン 基準価額
37,074 円
▲ 225 円 (0.61%)（前日比）
基準日: 2026年5月22日

## 仕組み

GitHub Actions（毎平日朝）→ 投資信託協会から基準価額を取得 → LINEに送信

## 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3 |
| データ取得 | requests / BeautifulSoup4 |
| データ取得元 | 投資信託協会 |
| 通知 | LINE Messaging API |
| 自動実行 | GitHub Actions（cron） |

## スケジュール

平日（月〜金）朝8時頃にLINEに届きます。  
※ GitHub Actionsの混雑により30分〜1時間遅れる場合があります。

## 費用

完全無料（GitHub Actions + LINE Messaging API 無料枠）
