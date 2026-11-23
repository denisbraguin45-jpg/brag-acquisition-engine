import json
import sqlite3
from pathlib import Path

demos_dir = Path("D:/app/brag-lead-hunter/demos")
print("demos_dir exists?", demos_dir.exists())

# Database check
db_path = Path("D:/app/brag-lead-hunter/data/brag_lead_hunter.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print("Tables in brag_lead_hunter.db:", tables)
    for t in tables:
        c.execute(f"SELECT count(*) FROM {t}")
        print(f"  {t}: {c.fetchone()[0]} rows")
    conn.close()

# Demos data check
db_demos_path = demos_dir / "database_all_demos.json"
if db_demos_path.exists():
    with open(db_demos_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Total records in database_all_demos.json:", len(data))
    print("Sample record keys:", list(data[0].keys()))

crm_leads_path = demos_dir / "crm_all_leads.json"
if crm_leads_path.exists():
    with open(crm_leads_path, "r", encoding="utf-8") as f:
        crm = json.load(f)
    print("Total records in crm_all_leads.json:", len(crm))
