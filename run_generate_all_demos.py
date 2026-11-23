import sys
import time
sys.path.insert(0, "D:/app/brag-lead-hunter")
from backend import demo_builder
import sqlite3

print("Starting generation of 60 top demos (30 Denis with Campello Racing theme + 30 Gabriel)...")
t0 = time.time()
conn = sqlite3.connect("D:/app/brag-lead-hunter/data/brag_lead_hunter.db")
manifest = demo_builder.generate_top_30_demos(conn=conn)
conn.close()
t1 = time.time()
print(f"Done in {t1 - t0:.2f} seconds. Total items in manifest: {len(manifest)}")

denis = [m for m in manifest if m.get("owner") == "denis"]
gabriel = [m for m in manifest if m.get("owner") == "gabriel"]

print(f"Denis demos count: {len(denis)}")
print(f"Gabriel demos count: {len(gabriel)}")

print("\nFirst 3 Denis demos:")
for d in denis[:3]:
    print(f" #{d.get('partner_rank')}: {d['slug']} | {d['name']} | Archetype: {d['archetype']} | WA: {d['phone_display']}")

print("\nFirst 3 Gabriel demos:")
for g in gabriel[:3]:
    print(f" #{g.get('partner_rank')}: {g['slug']} | {g['name']} | Archetype: {g['archetype']} | WA: {g['phone_display']}")
