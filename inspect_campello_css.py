import urllib.request
import re

url = "https://campello-racing.vercel.app/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

# Find css link
css_files = re.findall(r'href=["\'](/_next/static/immutable/chunks/[^"\']+\.css)["\']', html)
print("CSS files:", css_files)

if css_files:
    css_url = "https://campello-racing.vercel.app" + css_files[0]
    css = urllib.request.urlopen(css_url).read().decode("utf-8", errors="ignore")
    print("CSS length:", len(css))
    
    # search for root colors, fonts, theme variables
    root_vars = re.findall(r'--[a-zA-Z0-9_-]+:[^;]+;', css[:3000])
    print("CSS vars sample:")
    for v in root_vars[:20]:
        print(" ", v)
        
    fonts = re.findall(r'font-family:[^;}]+', css)
    print("Fonts sample:", list(set(fonts))[:10])
