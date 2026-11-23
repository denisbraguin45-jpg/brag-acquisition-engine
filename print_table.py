import json

with open("D:/app/brag-lead-hunter/demos/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

denis = [m for m in manifest if m.get("owner") == "denis"]
for i, d in enumerate(denis, 1):
    print(f"| #{i:02d} | **{d['name']}** | {d['city']}/{d['state']} | `{d['phone_display']}` | [{d['slug']}](https://brag-showroom-demos.vercel.app/{d['slug']}) | [Disparar WhatsApp]({d['whatsapp_send_url']}) |")
