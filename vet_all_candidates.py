import sqlite3, json

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

# Get existing demos in directory
import os
existing_demos = set(os.listdir('D:/app/brag-lead-hunter/demos'))
print("Existing demo folders count:", len(existing_demos))

# Inspect AUDITS where audit_status in ('broken', 'third_party_only', 'none', 'no_website') or has_own_website=0
query = """
SELECT c.id, c.name, c.city, c.state, c.niche, c.address,
       s.username, s.profile_name, s.latest_post_date, s.followers_count, s.posts_count, s.external_url, s.public_phone,
       a.audit_status, a.issues_found, a.url_tested
FROM COMPANIES c
JOIN SOCIAL_PROFILES s ON c.id = s.company_id
LEFT JOIN AUDITS a ON c.id = a.company_id
WHERE s.platform = 'instagram'
  AND s.latest_post_date >= '2026-08-01'
  AND (c.has_own_website = 0 OR a.audit_status IN ('broken', 'third_party_only', 'social_only', 'no_website', 'non_functional'))
ORDER BY s.followers_count DESC
"""
cur.execute(query)
candidates = cur.fetchall()
print(f"Total verified active candidates with NO functional own website: {len(candidates)}")

with open('D:/app/brag-lead-hunter/demos/sales_distribution_400.json', 'r', encoding='utf-8') as f:
    sales = json.load(f)

# Leads currently in sales
sales_instas = {s.get('instagram_handle', '').lower().strip().replace('@', ''): s for s in sales if s.get('instagram_handle')}
sales_names = {s['company_name'].lower().strip(): s for s in sales}

# Leads that actually have live demos right now
sales_with_demo = {s.get('instagram_handle', '').lower().strip().replace('@', ''): s for s in sales if s.get('demo_url') and s.get('demo_url').strip()}
print(f"Sales leads with existing demo_url: {len(sales_with_demo)}")

# Let's inspect which of these candidates either:
# 1) Don't have a demo yet (even if in sales or not in sales)
# 2) Are fresh and meet 100% of the criteria:
#    - Valid active instagram with verified latest_post_date >= 2026-08-01 (< 120 days ago!)
#    - Broken or third-party/no own website
#    - Clean name and city
valid_targets = []
for c in candidates:
    cid, name, city, state, niche, addr, u, pname, post_date, followers, posts, ext_url, phone, a_status, issues, url_tested = c
    u_clean = u.lower().strip().replace('@', '')
    
    # check if already has demo
    slug = u_clean.replace('_', '-').replace('.', '-')
    has_demo = slug in existing_demos or (f"demo-{slug}" in existing_demos)
    
    # check website
    ext_lower = (ext_url or '').lower()
    has_real_site = False
    if ext_lower and not any(k in ext_lower for k in ['linktr.ee', 'wa.me', 'whatsapp', 'bit.ly', 'instabio', 'bio.link', 'contate.me', 'beacons.ai', 'canva.com', 'mercadolivre.com.br']):
        if a_status not in ['broken', 'third_party_only']:
            has_real_site = True
            
    if has_real_site:
        continue
        
    valid_targets.append({
        'cid': cid,
        'company_name': name,
        'city': city,
        'state': state,
        'segment': niche,
        'address': addr,
        'instagram': u_clean,
        'profile_name': pname,
        'post_date': post_date,
        'followers': followers,
        'posts': posts,
        'phone': phone,
        'ext_url': ext_url,
        'audit_status': a_status,
        'in_sales': u_clean in sales_instas,
        'has_demo': has_demo
    })

print(f"Total strictly vetted candidates (<120 days, active IG, no website): {len(valid_targets)}")
targets_without_demo = [t for t in valid_targets if not t['has_demo']]
print(f"Targets without existing demo: {len(targets_without_demo)}")

for i, t in enumerate(targets_without_demo[:35]):
    print(f"{i+1:02d}. @{t['instagram']} | {t['company_name']} | {t['city']}/{t['state']} | {t['segment']} | Posts: {t['posts']} | Foll: {t['followers']} | InSales: {t['in_sales']}")

conn.close()
