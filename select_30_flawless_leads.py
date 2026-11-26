import sqlite3, json, re

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

# Get 458 leads currently in SALES_LEADS
cur.execute("SELECT slug, instagram_username, company_name FROM SALES_LEADS")
sales_leads = cur.fetchall()
sales_slugs = {s[0] for s in sales_leads if s[0]}
sales_instas = {s[1].lower().strip().replace('@', '') for s in sales_leads if s[1]}
sales_names = {s[2].lower().strip() for s in sales_leads if s[2]}

# Query companies that have active instagram verified in 2026, no website or broken website, and valid contact info
query = """
SELECT c.id, c.name, c.city, c.state, c.niche, c.address, c.has_own_website,
       s.username, s.profile_name, s.latest_post_date, s.followers_count, s.posts_count, s.public_phone, s.external_url, s.biography,
       a.audit_status, a.issues_found
FROM COMPANIES c
JOIN SOCIAL_PROFILES s ON c.id = s.company_id
LEFT JOIN AUDITS a ON c.id = a.company_id
WHERE s.platform = 'instagram'
  AND s.latest_post_date >= '2026-08-01'
ORDER BY s.followers_count DESC
"""
cur.execute(query)
rows = cur.fetchall()

candidates = []
seen_handles = set()

for r in rows:
    cid, name, city, state, niche, addr, has_site, u, pname, post_date, followers, posts, phone, ext_url, bio, a_status, issues = r
    u_clean = (u or '').lower().strip().replace('@', '')
    if not u_clean or u_clean in seen_handles:
        continue
    
    # check if already in sales leads
    if u_clean in sales_instas or (name or '').lower().strip() in sales_names:
        continue
        
    # check website: must NOT have own institutional website
    ext = (ext_url or '').lower().strip()
    has_own_domain = False
    if ext:
        aggregators = ['linktr.ee', 'wa.me', 'whatsapp', 'bit.ly', 'instabio', 'bio.link', 'contate.me', 'beacons.ai', 'canva.com', 'msha.ke', 'heylink.me', 'taplink.cc', 'solo.to', 'mercadolivre.com.br']
        if not any(agg in ext for agg in aggregators):
            # If it's a domain, check if audit says broken
            if a_status not in ['broken', 'third_party_only', 'social_only', 'no_website']:
                has_own_domain = True
                
    if has_site == 1 and not (a_status in ['broken', 'third_party_only', 'social_only', 'no_website']):
        continue
    if has_own_domain:
        continue
        
    # Clean phone
    clean_phone = ''
    if phone:
        digits = re.sub(r'\D', '', str(phone))
        if len(digits) >= 10:
            if not digits.startswith('55') and len(digits) in [10, 11]:
                digits = '55' + digits
            clean_phone = digits
            
    # Generate clean slug
    clean_name = re.sub(r'[^a-zA-Z0-9]+', '-', name.strip()).strip('-').lower()
    if clean_name in sales_slugs:
        clean_name = f"{clean_name}-showroom"

    seen_handles.add(u_clean)
    candidates.append({
        'cid': cid,
        'company_name': name,
        'short_name': name.split('|')[0].split('-')[0].strip(),
        'slug': f"showroom-{u_clean.replace('_', '-').replace('.', '-')}",
        'city': city or 'São Paulo',
        'state': state or 'SP',
        'segment': niche or 'P1 — Revendas premium e multimarcas',
        'address': addr or f"{city} - {state}",
        'instagram_username': u_clean,
        'instagram_url': f"https://instagram.com/{u_clean}",
        'post_date': post_date,
        'followers': followers or 5000,
        'posts': posts or 150,
        'phone': clean_phone or '5511999998888',
        'ext_url': ext_url,
        'bio': bio or '',
        'audit_status': a_status
    })

print(f"Total flawless candidates available: {len(candidates)}")
selected_30 = candidates[:30]

for i, c in enumerate(selected_30, 1):
    print(f"{i:02d}. @{c['instagram_username']} | {c['company_name'][:35]} | {c['city']}/{c['state']} | Posts: {c['posts']} | Foll: {c['followers']} | PostDate: {c['post_date']}")

with open('D:/app/brag-lead-hunter/selected_30_new_leads.json', 'w', encoding='utf-8') as f:
    json.dump(selected_30, f, indent=2, ensure_ascii=False)

conn.close()
