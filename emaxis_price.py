import requests, os
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

r = requests.get("https://emaxis.am.mufg.jp/mukamapi/fund_details/?fund_cd=253425", headers=HEADERS, timeout=10)
data = r.json()["datasets"]

price    = int(data["cfm_base_price"])
changes  = float(data["cfm_price_changes"])
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
