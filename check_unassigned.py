import sqlite3, json

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

# Get sales leads usernames
cur.execute("SELECT instagram_username, company_name FROM SALES_LEADS")
sales_leads = cur.fetchall()
sales_instas = {s[0].lower().strip().replace('@', '') for s in sales_leads if s[0]}
sales_names = {s[1].lower().strip() for s in sales_leads if s[1]}
print(f"SALES_LEADS count: {len(sales_leads)}")

query = """
SELECT c.id, c.name, c.city, c.state, c.niche, c.has_own_website,
       s.username, s.latest_post_date, s.followers_count, s.posts_count, s.public_phone, s.external_url
FROM COMPANIES c
JOIN SOCIAL_PROFILES s ON c.id = s.company_id
WHERE s.platform = 'instagram'
"""
cur.execute(query)
rows = cur.fetchall()
print(f"Total Companies with Instagram profile in DB: {len(rows)}")

unassigned = []
for r in rows:
    cid, name, city, state, niche, has_site, username, post_date, followers, posts, phone, ext_url = r
    u_clean = (username or '').lower().strip().replace('@', '')
    n_clean = (name or '').lower().strip()
    
    if u_clean in sales_instas or n_clean in sales_names:
        continue
    
    unassigned.append({
        'cid': cid,
        'name': name,
        'city': city,
        'state': state,
        'niche': niche,
        'has_site': has_site,
        'username': username,
        'latest_post_date': post_date,
        'followers': followers,
        'posts': posts,
        'phone': phone,
        'ext_url': ext_url
    })

print(f"Unassigned companies with Instagram in DB: {len(unassigned)}")
for u in unassigned[:20]:
    print(u)
conn.close()
