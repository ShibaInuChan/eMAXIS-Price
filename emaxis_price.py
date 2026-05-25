import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

for name, url in [
    ("toushin",     "https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000?isinCd=JP90C000H1T1"),
    ("morningstar", "https://www.morningstar.co.jp/fund/sr_detail/detail.do?isin=JP90C000H1T1"),
]:
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
    print(f"=== {name} ===")
    for line in lines[:50]:
        if any(c.isdigit() for c in line):
            print(line)
