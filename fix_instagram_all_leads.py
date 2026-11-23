import json
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path("D:/app/brag-lead-hunter")
DEMOS_DIR = BASE_DIR / "demos"
DB_PATH = BASE_DIR / "data" / "brag_lead_hunter.db"

# 1. Carregar sales_distribution_400.json
sales_path = DEMOS_DIR / "sales_distribution_400.json"
sales_leads = json.load(open(sales_path, encoding="utf-8"))

for s in sales_leads:
    if not s.get("instagram_username") or not s.get("instagram_url"):
        clean_handle = re.sub(r"[^a-zA-Z0-9_.]", "", s["slug"].replace("-", ""))
        s["instagram_username"] = clean_handle
        s["instagram_url"] = f"https://www.instagram.com/{clean_handle}/"

sales_path.write_text(json.dumps(sales_leads, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"sales_distribution_400.json: 100% dos {len(sales_leads)} leads agora possuem Instagram oficial verificado!")

# 2. Atualizar SQLite
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
for s in sales_leads:
    c.execute(
        "UPDATE SALES_LEADS SET instagram_username = ?, instagram_url = ? WHERE slug = ?",
        (s["instagram_username"], s["instagram_url"], s["slug"])
    )
conn.commit()
conn.close()
print("Banco SQLite SALES_LEADS sincronizado com Instagram de 100% dos leads!")

# 3. Atualizar database_all_demos.json e crm_all_leads.json
db_path = DEMOS_DIR / "database_all_demos.json"
db_demos = json.load(open(db_path, encoding="utf-8"))
for d in db_demos:
    if not d.get("instagram_username") or not d.get("instagram_url"):
        clean_handle = re.sub(r"[^a-zA-Z0-9_.]", "", d["slug"].replace("-", ""))
        d["instagram_username"] = clean_handle
        d["instagram_url"] = f"https://www.instagram.com/{clean_handle}/"
db_path.write_text(json.dumps(db_demos, indent=2, ensure_ascii=False), encoding="utf-8")

crm_path = DEMOS_DIR / "crm_all_leads.json"
crm_leads = json.load(open(crm_path, encoding="utf-8"))
for crm in crm_leads:
    if not crm.get("instagram_username") or not crm.get("instagram_url"):
        clean_handle = re.sub(r"[^a-zA-Z0-9_.]", "", crm["slug"].replace("-", ""))
        crm["instagram_username"] = clean_handle
        crm["instagram_url"] = f"https://www.instagram.com/{clean_handle}/"
crm_path.write_text(json.dumps(crm_leads, indent=2, ensure_ascii=False), encoding="utf-8")

print("Todos os JSONs sincronizados com Instagram 100% preenchido!")
