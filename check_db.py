import json
import sqlite3
from pathlib import Path

# Connect to database or inspect existing leads
conn = sqlite3.connect("D:/app/brag-lead-hunter/data/leads.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", c.fetchall())

# Count leads by status/niche
try:
    c.execute("SELECT count(*) FROM leads")
    print("Total leads:", c.fetchone()[0])
except Exception as e:
    print("Error:", e)
conn.close()
