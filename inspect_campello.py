import urllib.request
import re

url = "https://campello-racing.vercel.app/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

title = re.search(r'<title>(.*?)</title>', html)
print("Title:", title.group(1) if title else "None")

h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
print("H1s:", [re.sub(r'<[^>]+>', '', x).strip() for x in h1s])

h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
print("H2s:", [re.sub(r'<[^>]+>', '', x).strip() for x in h2s[:10]])

section_ids = re.findall(r'<section[^>]*id=["\'](.*?)["\']', html)
print("Section IDs:", section_ids)

texts = re.findall(r'>([^<]{25,120})<', html)
clean_texts = [t.strip() for t in texts if t.strip() and not t.strip().startswith("{")]
print("Sample Texts:")
for t in clean_texts[:20]:
    print(" -", t)
