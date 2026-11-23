import json

with open("D:/app/brag-lead-hunter/demos/demos_100_novas.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Total: {len(items)}")
for i, d in enumerate(items[:20], 1):
    print(f"| #{i:02d} | **{d['name']}** | {d['city']}/{d['state']} | `{d['phone_display']}` | [{d['slug']}](https://brag-showroom-demos.vercel.app/{d['slug']}) | [Disparar WhatsApp]({d['whatsapp_send_url']}) |")
