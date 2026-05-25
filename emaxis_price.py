import requests, os, re
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import date, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

def fetch_toushin(isin):
    try:
        r = requests.get(f"https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000?isinCd={isin}", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        price = change = date_str = pct = None
        for line in lines:
            if "基準日" in line:
                m = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', line)
                if m:
                    date_str = m.group()
            if re.match(r'^\d{1,3},\d{3}$', line) and price is None:
                price = int(line.replace(",", ""))
            if price and change is None and re.match(r'^-?\d{1,4}$', line):
                change = int(line)
            if re.match(r'^\([+-]?\d+\.\d+%\)$', line) and pct is None:
                pct = line.strip("()")
        return price, change, date_str, pct
    except:
        return None, None, None, None

def fetch_stooq(symbol):
    try:
        d2 = date.today().strftime("%Y%m%d")
        d1 = (date.today() - timedelta(days=10)).strftime("%Y%m%d")
        url = f"https://stooq.com/q/d/l/?s={quote(symbol)}&d1={d1}&d2={d2}&i=d"
        r = requests.get(url, timeout=10)
        rows = [l for l in r.text.strip().split("\n")[1:] if l.strip()]
        if len(rows) < 2:
            return None, None, None
        curr = rows[-1].split(",")
        prev = rows[-2].split(",")
        price = float(curr[4])
        prev_price = float(prev[4])
        change = round(price - prev_price, 4)
        pct = round(change / prev_price * 100, 2)
        return price, change, pct
    except:
        return None, None, None

def fetch_crypto():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,ripple", "vs_currencies": "jpy", "include_24hr_change": "true"},
            timeout=10
        )
        return r.json()
    except:
        return {}

def fetch_tanaka_gold():
    try:
        r = requests.get("https://gold.tanaka.co.jp/commodity/souba/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            texts = [c.get_text(strip=True) for c in cells]
            if texts and re.fullmatch(r'金', texts[0]):
                prices = []
                for t in texts[1:]:
                    m = re.search(r'([\d,]+)', t)
                    if m:
                        v = int(m.group().replace(",", ""))
                        if 5000 <= v <= 30000:
                            prices.append(v)
                if prices:
                    return prices[0]
        return None
    except:
        return None

def sgn(v):
    return "▲" if (v or 0) >= 0 else "▼"

def fmt(v, d=0):
    if v is None:
        return "---"
    return f"{v:,.{d}f}" if d else f"{round(v):,}"

def fund_line(name, data):
    price, change, date_str, pct = data
    if price is None:
        return f"{name}: 取得失敗"
    return f"{name}: {fmt(price)} 円  {sgn(change)} {fmt(abs(change or 0))} ({pct})  {date_str}"

def stock_line(name, data, d=0):
    price, change, pct = data
    if price is None:
        return f"{name}: 取得失敗"
    return f"{name}: {fmt(price, d)} 円  {sgn(change)} {fmt(abs(change or 0), d)} ({fmt(pct, 2)}%)"

def crypto_line(name, dct):
    p = dct.get("jpy")
    c = dct.get("jpy_24h_change")
    if p is None:
        return f"{name}: 取得失敗"
    return f"{name}: {fmt(p)} 円  {sgn(c)} {fmt(abs(c or 0), 2)}%"

orkan  = fetch_toushin("JP90C000H1T1")
sp500  = fetch_toushin("JP90C000H474")
aeon   = fetch_stooq("8267.JP")
nikkei = fetch_stooq("^NKX")
usdjpy = fetch_stooq("USDJPY")
gold   = fetch_tanaka_gold()
crypto = fetch_crypto()

btc = crypto.get("bitcoin", {})
eth = crypto.get("ethereum", {})
xrp = crypto.get("ripple", {})

fx_line = f"ドル円: {fmt(usdjpy[0], 2)} 円  {sgn(usdjpy[1])} {fmt(abs(usdjpy[1] or 0), 2)} ({fmt(usdjpy[2], 2)}%)" if usdjpy[0] else "ドル円: 取得失敗"
gold_line = f"金（田中貴金属）: {fmt(gold)} 円/g" if gold else "金（田中貴金属）: 取得失敗"

message = "\n".join([
    "📊 本日の資産価格",
    "",
    "【投資信託】",
    fund_line("オルカン", orkan),
    fund_line("S&P500", sp500),
    "",
    "【株式・指数】",
    stock_line("イオン(8267)", aeon),
    stock_line("日経平均", nikkei),
    "",
    "【為替】",
    fx_line,
    "",
    "【金】",
    gold_line,
    "",
    "【暗号資産】",
    crypto_line("BTC", btc),
    crypto_line("ETH", eth),
    crypto_line("XRP", xrp),
])

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
