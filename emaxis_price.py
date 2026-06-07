import requests, os, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

ISIN_ORKAN = "JP90C000H1T1"

r = requests.get(f"https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000?isinCd={ISIN_ORKAN}", headers=HEADERS, timeout=10)
print("[DEBUG] status:", r.status_code)
soup = BeautifulSoup(r.text, "html.parser")
lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
print("[DEBUG] ---- text lines around price/change ----")
for i, l in enumerate(lines):
    if re.match(r'^\d{1,3},\d{3}$', l) or re.match(r'^-?\d{1,4}$', l) or re.match(r'^\(.*%\)$', l) or "前日" in l or "騰落" in l or "基準価額" in l:
        print(i, repr(l))

print("[DEBUG] ---- raw HTML around 前日比 ----")
idx = r.text.find("前日比")
while idx != -1 and idx < len(r.text):
    print(repr(r.text[max(0, idx-300):idx+300]))
    print("----")
    idx = r.text.find("前日比", idx + 1)
    if idx > 20000:
        break
