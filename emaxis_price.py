import requests, os, re
from bs4 import BeautifulSoup
import yfinance as yf

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

ISIN_ORKAN = "JP90C000H1T1"
ISIN_SP500 = "JP90C000GKC6"

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

        # 前日比の符号はテキストに含まれず、fds-positive/negative-number-fg の
        # ラッパー要素（と矢印アイコン）でのみ表現されているため、別途判定する
        fg = soup.select_one(".fds-positive-number-fg, .fds-negative-number-fg")
        if fg and change is not None:
            is_negative = "fds-negative-number-fg" in (fg.get("class") or [])
            change = -abs(change) if is_negative else abs(change)
            if pct and not pct.startswith(("+", "-")):
                pct = f"{'-' if is_negative else '+'}{pct}"

        print(f"[DEBUG] toushin {isin}: price={price}, change={change}, date={date_str}")
        return price, change, date_str, pct
    except Exception as e:
        print(f"[ERROR] toushin {isin}: {e}")
        return None, None, None, None

def fetch_yf(symbol):
    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info
        price = float(fi.last_price)
        prev = float(fi.previous_close)
        print(f"[DEBUG] yf {symbol}: price={price:.2f}, prev_close={prev:.2f}")
        change = round(price - prev, 4)
        pct = round(change / prev * 100, 2)
        return price, change, pct
    except Exception as e:
        print(f"[ERROR] yf {symbol}: {e}")
        return None, None, None

def fetch_crypto():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,ripple", "vs_currencies": "jpy", "include_24hr_change": "true"},
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"[ERROR] crypto: {e}")
        return {}

def fetch_tanaka_gold():
    try:
        r = requests.get("https://gold.tanaka.co.jp/commodity/souba/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            texts = [c.get_text(strip=True) for c in cells]
            # 構造: ['金', '25,917 円', '+253 円', '25,368 円', '+61 円', '価格推移']
            if len(texts) >= 3 and re.fullmatch(r'金', texts[0]):
                pm = re.search(r'([\d,]+)', texts[1])
                cm = re.search(r'([+-]?\d+)', texts[2])
                price = int(pm.group().replace(",", "")) if pm else None
                change = int(cm.group()) if cm else None
                return price, change
        return None, None
    except Exception as e:
        print(f"[ERROR] tanaka: {e}")
        return None, None

def trend(v):
    if v is None:
        return "➖"
    return "📈" if v >= 0 else "📉"

def sgn(v):
    return "▲" if (v or 0) >= 0 else "▼"

def fmt(v, d=0):
    if v is None:
        return "---"
    return f"{v:,.{d}f}" if d else f"{round(v):,}"

def fund_line(name, data):
    price, change, _, pct = data
    if price is None:
        return f"➖ {name}: 取得失敗"
    return f"{trend(change)} {name}: {fmt(price)} 円  {sgn(change)} {fmt(abs(change or 0))} ({pct})"

def stock_line(name, data, d=0):
    price, change, pct = data
    if price is None:
        return f"➖ {name}: 取得失敗"
    return f"{trend(change)} {name}: {fmt(price, d)} 円  {sgn(change)} {fmt(abs(change or 0), d)} ({fmt(pct, 2)}%)"

def crypto_line(name, dct):
    p = dct.get("jpy")
    c = dct.get("jpy_24h_change")
    if p is None:
        return f"➖ {name}: 取得失敗"
    return f"{trend(c)} {name}: {fmt(p)} 円  {sgn(c)} {fmt(abs(c or 0), 2)}%"

orkan  = fetch_toushin(ISIN_ORKAN)
sp500  = fetch_toushin(ISIN_SP500)
aeon   = fetch_yf("8267.T")
nikkei = fetch_yf("^N225")
usdjpy = fetch_yf("USDJPY=X")
gold, gold_change = fetch_tanaka_gold()
crypto = fetch_crypto()

btc = crypto.get("bitcoin", {})
eth = crypto.get("ethereum", {})
xrp = crypto.get("ripple", {})

date_str = orkan[2] or ""
header = f"📊 本日の資産価格（{date_str}）" if date_str else "📊 本日の資産価格"

if usdjpy[0]:
    fx_line = f"{trend(usdjpy[1])} ドル円: {fmt(usdjpy[0], 2)} 円  {sgn(usdjpy[1])} {fmt(abs(usdjpy[1] or 0), 2)} ({fmt(usdjpy[2], 2)}%)"
else:
    fx_line = "➖ ドル円: 取得失敗"

if gold:
    gold_line = f"{trend(gold_change)} 金（田中貴金属）: {fmt(gold)} 円/g"
else:
    gold_line = "➖ 金（田中貴金属）: 取得失敗"

message = "\n".join([
    header,
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

print('[DIAG] skipping LINE push for verification run')
print(message)
