import json, sqlite3

with open('D:/app/brag-lead-hunter/demos/sales_distribution_400.json', 'r', encoding='utf-8') as f:
    sales = json.load(f)

print('Total sales leads:', len(sales))
companies_sales = {s['company_name'].lower().strip(): s for s in sales}
instas_sales = {s.get('instagram_handle', '').lower().strip().replace('@', ''): s for s in sales if s.get('instagram_handle')}

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()
cur.execute("SELECT id, name, segment, city, state, phone FROM COMPANIES")
all_companies = cur.fetchall()
print('Total COMPANIES in DB:', len(all_companies))

cur.execute("SELECT company_id, platform, handle, profile_url FROM SOCIAL_PROFILES")
all_profiles = cur.fetchall()
print('Total SOCIAL_PROFILES in DB:', len(all_profiles))

cur.execute("SELECT company_id, url FROM WEBSITES")
all_websites = cur.fetchall()
print('Total WEBSITES in DB:', len(all_websites))

profiles_by_company = {}
for cid, plat, handle, purl in all_profiles:
    if plat.lower() == 'instagram':
        profiles_by_company[cid] = (handle, purl)

websites_by_company = {}
for cid, url in all_websites:
    websites_by_company[cid] = url

candidates = []
for cid, name, seg, city, state, phone in all_companies:
    n_lower = name.lower().strip()
    p_info = profiles_by_company.get(cid)
    handle = p_info[0] if p_info else ''
    h_clean = handle.lower().strip().replace('@', '') if handle else ''
    
    # check if in sales
    if n_lower in companies_sales:
        continue
    if h_clean and h_clean in instas_sales:
        continue
    
    site = websites_by_company.get(cid, '')
    candidates.append({
        'cid': cid,
        'name': name,
        'segment': seg,
        'city': city,
        'state': state,
        'phone': phone,
        'handle': handle,
        'site': site
    })

print(f'Candidates in COMPANIES not in sales_distribution: {len(candidates)}')
for c in candidates[:15]:
    print(c)
