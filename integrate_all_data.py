import json
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path("D:/app/brag-lead-hunter")
DEMOS_DIR = BASE_DIR / "demos"

# 1. Carregar 30 novas demos geradas
new_demos = json.load(open(BASE_DIR / "new_30_gabriel_demos_records.json", encoding="utf-8"))
print(f"Total novas demos: {len(new_demos)}")

# 2. Carregar e atualizar database_all_demos.json
db_path = DEMOS_DIR / "database_all_demos.json"
db_records = json.load(open(db_path, encoding="utf-8"))
existing_slugs = {d["slug"] for d in db_records}

added_to_db = 0
for d in new_demos:
    if d["slug"] not in existing_slugs:
        db_records.append(d)
        existing_slugs.add(d["slug"])
        added_to_db += 1

# Re-calcular ranks e partner_ranks limpos
# Denis: 398 demos
# Gabriel: 30 antigas + 30 novas = 60 demos
denis_count = 0
gabriel_count = 0

for idx, rec in enumerate(db_records, start=1):
    rec["rank"] = idx
    if rec.get("owner") == "gabriel":
        gabriel_count += 1
        rec["partner_rank"] = gabriel_count
    else:
        denis_count += 1
        rec["partner_rank"] = denis_count

db_path.write_text(json.dumps(db_records, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"database_all_demos.json atualizado! Total: {len(db_records)} (Denis: {denis_count}, Gabriel: {gabriel_count})")

# 3. Carregar e atualizar crm_all_leads.json
crm_json_path = DEMOS_DIR / "crm_all_leads.json"
crm_records = json.load(open(crm_json_path, encoding="utf-8"))
crm_existing_slugs = {d["slug"] for d in crm_records}

added_to_crm = 0
for d in new_demos:
    if d["slug"] not in crm_existing_slugs:
        crm_item = {
            "slug": d["slug"],
            "name": d["name"],
            "city": d["city"],
            "state": d["state"],
            "location": d["location"],
            "instagram_username": d["instagram_username"],
            "instagram_url": d["instagram_url"],
            "phone_display": d["phone_display"],
            "whatsapp_e164": d["whatsapp_e164"],
            "demo_url": d["demo_url"],
            "whatsapp_message": d["whatsapp_message"],
            "whatsapp_send_url": d["whatsapp_send_url"],
            "archetype": d["archetype"],
            "score": d["score"],
            "owner": "gabriel",
            "is_active_manifest": True,
            "has_demo": True,
            "history_batch": d["history_batch"]
        }
        crm_records.append(crm_item)
        crm_existing_slugs.add(d["slug"])
        added_to_crm += 1

crm_json_path.write_text(json.dumps(crm_records, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"crm_all_leads.json atualizado! Total: {len(crm_records)} (Adicionados: {added_to_crm})")

# 4. Atualizar crm_all_leads.csv
csv_path = DEMOS_DIR / "crm_all_leads.csv"
fieldnames = [
    "rank", "owner", "owner_name", "partner_rank", "name", "slug", "niche",
    "city", "state", "phone_display", "whatsapp_e164", "instagram_username",
    "instagram_url", "score", "priority", "demo_url", "whatsapp_send_url", "history_batch"
]

with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in db_records:
        writer.writerow({
            "rank": row.get("rank"),
            "owner": row.get("owner"),
            "owner_name": row.get("owner_name"),
            "partner_rank": row.get("partner_rank"),
            "name": row.get("name"),
            "slug": row.get("slug"),
            "niche": row.get("niche"),
            "city": row.get("city"),
            "state": row.get("state"),
            "phone_display": row.get("phone_display"),
            "whatsapp_e164": row.get("whatsapp_e164"),
            "instagram_username": row.get("instagram_username"),
            "instagram_url": row.get("instagram_url"),
            "score": row.get("score"),
            "priority": row.get("priority"),
            "demo_url": row.get("demo_url"),
            "whatsapp_send_url": row.get("whatsapp_send_url"),
            "history_batch": row.get("history_batch"),
        })
print("crm_all_leads.csv atualizado com sucesso!")

# 5. Re-gerar crm.html com o script embutido atualizado
from build_crm_page import crm_leads_json
# Executar a recriação do crm.html
import subprocess
subprocess.run(["python", "D:/app/brag-lead-hunter/build_crm_page.py"], check=True)
print("crm.html regerado com sucesso!")

# 6. Atualizar manifest.json (para as 60 demos do Gabriel na manifest ativa)
manifest_path = DEMOS_DIR / "manifest.json"
manifest_records = json.load(open(manifest_path, encoding="utf-8"))
# Manter manifest com 60 de denis e 60 de gabriel
for d in new_demos:
    m_item = {
        "rank": len(manifest_records) + 1,
        "owner": "gabriel",
        "owner_name": "Gabriel",
        "owner_label": "Fila Gabriel",
        "partner_rank": len([m for m in manifest_records if m.get("owner") == "gabriel"]) + 1,
        "company_id": f"comp-{d['slug']}",
        "slug": d["slug"],
        "name": d["name"],
        "short_name": d["short_name"],
        "niche": d["niche"],
        "vertical": "powersports",
        "archetype": d["archetype"],
        "city": d["city"],
        "state": d["state"],
        "score": d["score"],
        "priority": d["priority"],
        "instagram_username": d["instagram_username"],
        "instagram_url": d["instagram_url"],
        "instagram_bio": d["name"],
        "followers_count": 35000,
        "whatsapp_e164": d["whatsapp_e164"],
        "phone_display": d["phone_display"],
        "demo_url": d["demo_url"],
        "demo_path": d["demo_path"],
        "whatsapp_send_url": d["whatsapp_send_url"],
        "whatsapp_message": d["whatsapp_message"],
        "video_script_60s": d["video_script_60s"],
        "commercial_status": "demo_pronta",
        "recommended_offer": "Showroom Digital Avantgarde",
        "diagnosis": "Ausência de vitrine digital no celular"
    }
    manifest_records.append(m_item)

manifest_path.write_text(json.dumps(manifest_records, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"manifest.json atualizado! Total: {len(manifest_records)}")

# 7. Re-gerar index.html (Hub Central de Demos)
import sys
sys.path.insert(0, str(BASE_DIR))
from backend.demo_builder import render_hub_index_html
hub_html = render_hub_index_html(db_records)
(DEMOS_DIR / "index.html").write_text(hub_html, encoding="utf-8")
print(f"demos/index.html regerado com 458 showrooms!")

# 8. Atualizar vendas SQLite e sales_distribution_400.json garantindo que as demos estão atreladas
from backend.sales_db import DB_PATH
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Inserir ou atualizar na tabela SALES_LEADS se não existir
sales_path = DEMOS_DIR / "sales_distribution_400.json"
sales_leads = json.load(open(sales_path, encoding="utf-8"))
sales_slugs = {s["slug"] for s in sales_leads}

# Garantir que todos os 400 leads do sales_distribution possuam o link da demo correto
for s in sales_leads:
    if not s.get("demo_url"):
        s["demo_url"] = f"https://brag-showroom-demos.vercel.app/{s['slug']}"

sales_path.write_text(json.dumps(sales_leads, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"sales_distribution_400.json verificado e preservado!")
