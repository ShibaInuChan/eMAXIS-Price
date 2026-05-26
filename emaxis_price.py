import requests, os, re
from bs4 import BeautifulSoup
import yfinance as yf

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

def find_sp500_isin():
    try:
        # 動作している詳細ページからナビリンクを取得してsearch URLを特定する
        r = requests.get(
            "https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000?isinCd=JP90C000H1T1",
            headers=HEADERS, timeout=10
        )
        soup = BeautifulSoup(r.text, "html.parser")

        # 全リンクをログ出力して調査
        for a in soup.find_all("a", href=True):
            print(f"[DEBUG] nav link: href={a['href'][:80]} text={a.get_text(strip=True)[:30]}")

        # 「ファンドを探す」「検索」等のリンクを探す
        search_url = None
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if any(k in text for k in ["ファンドを探す", "検索"]) and href and not href.startswith("#"):
                search_url = href if href.startswith("http") else f"https://toushin-lib.fwg.ne.jp{href}"
                print(f"[DEBUG] search_url: {search_url}")
                break

        # フォールバック: 代表的なパスを試す
        if not search_url:
            for url in [
                "https://toushin-lib.fwg.ne.jp/FdsWeb/FDST000000",
                "https://toushin-lib.fwg.ne.jp/FdsWeb/FDST020000",
            ]:
                r2 = requests.get(url, headers=HEADERS, timeout=5)
                print(f"[DEBUG] fallback {url}: {r2.status_code}")
                if r2.status_code == 200:
                    search_url = url
                    break

        if not search_url:
            return None

        # S&P500ファンドを検索
        r3 = requests.get(search_url, params={"fundNm": "eMAXIS Slim 米国株式"}, headers=HEADERS, timeout=10)
        print(f"[DEBUG] search result: status={r3.status_code} body={r3.text[:500]}")
        soup3 = BeautifulSoup(r3.text, "html.parser")
        for a in soup3.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "FDST030000" in href and "isinCd=" in href:
                m = re.search(r"isinCd=([A-Z0-9]+)", href)
                if m and any(k in text for k in ["S&P", "米国株式"]):
                    print(f"[DEBUG] found S&P500 ISIN: {m.group(1)}")
                    return m.group(1)
    except Exception as e:
        print(f"[ERROR] find_sp500_isin: {e}")
    return None

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
        print(f"[DEBUG] toushin {isin}: price={price}, change={change}, date={date_str}")
        return price, change, date_str, pct
    except Exception as e:
        print(f"[ERROR] toushin {isin}: {e}")
        return None, None, None, None

def fetch_yf(symbol):
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        print(f"[DEBUG] yf {symbol}: rows={len(hist)}, last={hist['Close'].iloc[-1] if len(hist) else 'N/A'}")
        if len(hist) < 1:
            return None, None, None
        price = float(hist["Close"].iloc[-1])
        if len(hist) >= 2:
            prev = float(hist["Close"].iloc[-2])
            change = round(price - prev, 4)
            pct = round(change / prev * 100, 2)
        else:
            change = pct = None
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
            if len(texts) >= 2 and re.fullmatch(r'金', texts[0]):
                m = re.search(r'([\d,]+)', texts[1])
                if m:
                    return int(m.group().replace(",", ""))
        return None
    except Exception as e:
        print(f"[ERROR] tanaka: {e}")
        return None

def sgn(v):
    return "▲" if (v or 0) >= 0 else "▼"

def fmt(v, d=0):
    if v is None:
        return "---"
    return f"{v:,.{d}f}" if d else f"{round(v):,}"

def fund_line(name, data):
    price, change, _, pct = data
    if price is None:
        return f"{name}: 取得失敗"
    return f"{name}: {fmt(price)} 円  {sgn(change)} {fmt(abs(change or 0))} ({pct})"

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

sp500_isin = find_sp500_isin()
orkan  = fetch_toushin("JP90C000H1T1")
sp500  = fetch_toushin(sp500_isin) if sp500_isin else (None, None, None, None)
aeon   = fetch_yf("8267.T")
nikkei = fetch_yf("^N225")
usdjpy = fetch_yf("USDJPY=X")
gold   = fetch_tanaka_gold()
crypto = fetch_crypto()

btc = crypto.get("bitcoin", {})
eth = crypto.get("ethereum", {})
xrp = crypto.get("ripple", {})

date_str = orkan[2] or ""
header = f"📊 本日の資産価格（{date_str}）" if date_str else "📊 本日の資産価格"
fx_line = f"ドル円: {fmt(usdjpy[0], 2)} 円  {sgn(usdjpy[1])} {fmt(abs(usdjpy[1] or 0), 2)} ({fmt(usdjpy[2], 2)}%)" if usdjpy[0] else "ドル円: 取得失敗"
gold_line = f"金（田中貴金属）: {fmt(gold)} 円/g" if gold else "金（田中貴金属）: 取得失敗"

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
