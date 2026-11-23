import json
from backend import demo_builder

with open("D:/app/brag-lead-hunter/demos/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

denis_manifest = [m for m in manifest if m.get("owner") == "denis"]
print(f"Current Denis manifest entries: {len(denis_manifest)}")
for m in denis_manifest:
    print(f" - {m['slug']}: {m['name']} (WA: {m.get('whatsapp')})")
