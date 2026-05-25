import requests, os
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

# 複数サイトを試してどれが使えるか確認
sources = [
    ("minkabu",    "https://minkabu.jp/fund/0331418A"),
    ("kabutan",    "https://kabutan.jp/stock/?code=0331418A"),
    ("toushin",    "https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000?isinCd=JP90C000H1T1"),
    ("morningstar","https://www.morningstar.co.jp/fund/sr_detail/detail.do?isin=JP90C000H1T1"),
]

for name, url in sources:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"{name}: {r.status_code}")
    except Exception as e:
        print(f"{name}: エラー {e}")
