import sqlite3

for db_path in ['D:/app/brag-lead-hunter/data/brag_lead_hunter.db', 'D:/app/brag-lead-hunter/data/leads.db']:
    print('=== DB:', db_path)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print('Tables:', tables)
        for t in tables:
            tname = t[0]
            cur.execute(f"SELECT count(*) FROM {tname}")
            print(f'  {tname}: {cur.fetchone()[0]} rows')
        conn.close()
    except Exception as e:
        print('Error:', e)
