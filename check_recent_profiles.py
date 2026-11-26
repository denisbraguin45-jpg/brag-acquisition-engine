import sqlite3, json

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

# Check all tables and row counts
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('Tables in DB:', tables)

# Check AUDITS table sample
cur.execute("SELECT * FROM AUDITS LIMIT 3")
print("Audits sample:", cur.fetchall())

# Check SOCIAL_PROFILES details for recent dates
cur.execute("""
    SELECT s.username, s.profile_name, s.latest_post_date, s.followers_count, s.posts_count, s.external_url, c.name, c.city, c.state, c.niche, c.address
    FROM SOCIAL_PROFILES s
    JOIN COMPANIES c ON s.company_id = c.id
    WHERE s.latest_post_date >= '2026-08-01'
    ORDER BY s.latest_post_date DESC
""")
recent_rows = cur.fetchall()
print(f"Total profiles with verified latest_post_date >= 2026-08-01: {len(recent_rows)}")
for r in recent_rows[:15]:
    print(r)

conn.close()
