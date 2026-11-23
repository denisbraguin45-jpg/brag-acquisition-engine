import json
from backend import demo_builder

with open("D:/app/brag-lead-hunter/demos/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

gabriel_manifest = [m for m in manifest if m.get("owner") == "gabriel"]
print(f"Current Gabriel manifest count: {len(gabriel_manifest)}")
for m in gabriel_manifest[:5]:
    print(f" #{m.get('partner_rank')}: {m['slug']} ({m['name']})")
