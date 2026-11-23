import urllib.request
import re

css_url = "https://campello-racing.vercel.app/_next/static/immutable/chunks/1e1h50bcw1evw.css"
css = urllib.request.urlopen(css_url).read().decode("utf-8", errors="ignore")

# Find color hexes
hexes = set(re.findall(r'#[0-9a-fA-F]{3,8}', css))
print("Hex colors in CSS:", sorted(list(hexes))[:30])

# Look for background colors or key classes
bg_matches = re.findall(r'background(?:-color)?:\s*([^;]+);', css)
print("Background samples:", list(set(bg_matches))[:10])
