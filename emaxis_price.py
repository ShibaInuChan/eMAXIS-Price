import requests, os, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

r = requests.get("https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000?isinCd=JP90C000H1T1", headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, "html.parser")
lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]

price = change = date = pct = None
for i, line in enumerate(lines):
    if "基準日" in line:
        m = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', line)
        if m:
            date = m.group()
    if re.match(r'^\d{2},\d{3}$', line) and price is None:
        price = int(line.replace(",", ""))
    if price and change is None and re.match(r'^-?\d{1,3}$', line):
        change = int(line)
    if re.match(r'^\([+-]?\d+\.\d+%\)$', line) and pct is None:
        pct = line.strip("()")

sign = "▲" if (change or 0) >= 0 else "▼"
message = f"""📈 オルカン 基準価額
{price:,} 円
{sign} {abs(change):,} 円 {pct}（前日比）
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
