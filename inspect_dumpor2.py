import urllib.request, re

url = "https://dumpor.io/v/gatti_veiculospremium"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Save 1500 chars after '<main'
main_idx = html.find('<main')
if main_idx != -1:
    print(html[main_idx:main_idx+2000])
else:
    print(html[5000:7000])
