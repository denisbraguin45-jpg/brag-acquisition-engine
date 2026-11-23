import sqlite3

for db in ['D:/app/brag-lead-hunter/data/brag_lead_hunter.db', 'D:/app/brag-lead-hunter/leads.db']:
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print(db, "Tables:", tables)
        for t in tables:
            tname = t[0]
            c.execute(f"SELECT count(*) FROM {tname};")
            print(f"  {tname} count:", c.fetchone()[0])
        conn.close()
    except Exception as e:
        print(db, "Error:", e)
