import sqlite3

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()
for table in ['COMPANIES', 'SOCIAL_PROFILES', 'WEBSITES', 'AUDITS', 'SALES_LEADS']:
    cur.execute(f"PRAGMA table_info({table});")
    cols = cur.fetchall()
    print(f"Table {table}: {[c[1] for c in cols]}")
conn.close()
