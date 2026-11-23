import sys
sys.path.insert(0, "D:/app/brag-lead-hunter")
from backend import demo_builder
import sqlite3

print("Testing select_top_30_nautical_leads...")
conn = sqlite3.connect("D:/app/brag-lead-hunter/data/brag_lead_hunter.db")
leads = demo_builder.select_top_30_nautical_leads(conn, limit=30)
print(f"Returned {len(leads)} nautical leads.")
for i, l in enumerate(leads[:5], 1):
    print(f" #{i}: {l['slug']} | {l['name']} | WA: {l['whatsapp']}")
conn.close()
