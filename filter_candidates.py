import sqlite3, datetime

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

# Get sales leads usernames
cur.execute("SELECT instagram_username, company_name FROM SALES_LEADS")
sales_leads = cur.fetchall()
sales_instas = {s[0].lower().strip().replace('@', '') for s in sales_leads if s[0]}
sales_names = {s[1].lower().strip() for s in sales_leads if s[1]}

query = """
SELECT c.id, c.name, c.city, c.state, c.niche, c.has_own_website,
       s.username, s.latest_post_date, s.followers_count, s.posts_count, s.public_phone, s.external_url,
       s.biography
FROM COMPANIES c
JOIN SOCIAL_PROFILES s ON c.id = s.company_id
WHERE s.platform = 'instagram'
"""
cur.execute(query)
rows = cur.fetchall()

candidates = []
for r in rows:
    cid, name, city, state, niche, has_site, username, post_date, followers, posts, phone, ext_url, bio = r
    u_clean = (username or '').lower().strip().replace('@', '')
    n_clean = (name or '').lower().strip()
    
    if not u_clean or u_clean in sales_instas or n_clean in sales_names:
        continue
    
    # Check external_url: if it is own website, skip
    ext = (ext_url or '').lower()
    has_own_domain = False
    if ext:
        # Check if it's social/link aggregator or whatsapp
        common_aggregators = ['linktr.ee', 'wa.me', 'whatsapp', 'bit.ly', 'instabio', 'bio.link', 'contate.me', 'beacons.ai', 'canva.com', 'msha.ke', 'heylink.me', 'taplink.cc', 'solo.to']
        if not any(agg in ext for agg in common_aggregators):
            has_own_domain = True
            
    if has_site == 1 or has_own_domain:
        continue
        
    # Check post date (must be within last 180 days from 2026-11-26, so after 2026-05-30)
    # latest_post_date format is YYYY-MM-DD
    days_old = None
    if post_date and post_date != 'None':
        try:
            p_dt = datetime.datetime.strptime(post_date[:10], '%Y-%m-%d')
            ref_dt = datetime.datetime(2026, 11, 26)
            days_old = (ref_dt - p_dt).days
        except Exception:
            pass
            
    # Check posts count and followers
    if posts and posts > 10 and (followers or 0) > 100:
        candidates.append({
            'cid': cid,
            'name': name,
            'city': city,
            'state': state,
            'niche': niche,
            'username': u_clean,
            'post_date': post_date,
            'days_old': days_old,
            'followers': followers,
            'posts': posts,
            'phone': phone,
            'ext_url': ext_url,
            'bio': bio
        })

print(f"Total pure Instagram-first candidates (<180 days, no website): {len(candidates)}")
# Sort by followers / activity
candidates.sort(key=lambda x: (x['days_old'] if x['days_old'] is not None else 999, -(x['followers'] or 0)))

for i, c in enumerate(candidates[:40]):
    print(f"{i+1:02d}. @{c['username']} | {c['name']} | {c['city']}/{c['state']} | Posts: {c['posts']} | Foll: {c['followers']} | LastPost: {c['post_date']} ({c['days_old']}d) | Ext: {c['ext_url']}")

conn.close()
