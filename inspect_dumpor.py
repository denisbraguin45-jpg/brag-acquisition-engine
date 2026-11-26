import urllib.request, re

url = "https://dumpor.io/v/gatti_veiculospremium"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# print snippets
print('Length:', len(html))
# search for post elements
posts = re.findall(r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
print('Posts matched:', len(posts))
# find any date-like text
for m in re.finditer(r'(ago|days|months|hours|min|2024|2025|2026)', html, re.IGNORECASE):
    snippet = html[max(0, m.start()-50):min(len(html), m.end()+50)]
    print('Match snippet:', snippet.replace('\n', ' '))
    break
