import requests, os
from datetime import datetime

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
})

# まずページを訪問してクッキーを取得
session.get("https://emaxis.am.mufg.jp/fund/253425.html", timeout=10)

# クッキーを持った状態でAPIを呼ぶ
session.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://emaxis.am.mufg.jp/fund/253425.html",
    "Origin": "https://emaxis.am.mufg.jp",
})

r = session.get("https://emaxis.am.mufg.jp/mukamapi/fund_details/?fund_cd=253425", timeout=10)
print("ステータス:", r.status_code)

# 静的チャートデータをフォールバックとして使う
if r.status_code != 200:
    r = session.get("https://emaxis.am.mufg.jp/fund_file/chart/chart_data_253425.js", timeout=10)
    print("フォールバック ステータス:", r.status_code)
    data_raw = r.json()
    last = data_raw["ROWS"][-1]
    price = int(last["BASE_PRICE"])
    base_date = last["BASE_DATE"]
    changes = 0
else:
    data = r.json()["datasets"]
    price = int(data["cfm_base_price"])
    changes = float(data["cfm_price_changes"])
    base_date = data["cfm_base_date"]

date = f"{base_date[:4]}年{base_date[4:6]}月{base_date[6:]}日"
sign = "▲" if changes >= 0 else "▼"

message = f"""📈 オルカン 基準価額
{price:,} 円
{sign} {abs(changes):,.0f} 円（前日比）
基準日: {date}"""

requests.post(
    "https://api.line.me/v2/bot/message/push",
    headers={
        "Authorization": f"Bearer {os.environ['LINE_TOKEN']}",
        "Content-Type": "application/json"
    },
    json={
        "to": os.environ["LINE_USER_ID"],
        "messages": [{"type": "text", "text": message}]
    }
)
print(message)
