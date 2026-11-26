import sqlite3, re

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

# Get phone numbers from SEARCH_HISTORY or AUDITS or SOCIAL_PROFILES biography
cur.execute("SELECT company_id, biography, public_phone FROM SOCIAL_PROFILES WHERE platform='instagram'")
bios = cur.fetchall()

phone_map = {}
for cid, bio, p_phone in bios:
    if p_phone:
        digits = re.sub(r'\D', '', str(p_phone))
        if len(digits) >= 10:
            phone_map[cid] = digits
            continue
    if bio:
        # search for phone pattern in bio
        matches = re.findall(r'(?:\(?\d{2}\)?\s*)?(?:9\s*)?\d{4}[-.\s]?\d{4}', bio)
        for m in matches:
            d = re.sub(r'\D', '', m)
            if len(d) in [10, 11]:
                phone_map[cid] = d
                break

print(f"Total phones extracted from bios/public_phone: {len(phone_map)}")

cur.execute("SELECT id, phone FROM COMPANIES WHERE phone IS NOT NULL AND phone != ''")
comp_phones = cur.fetchall()
for cid, p in comp_phones:
    d = re.sub(r'\D', '', str(p))
    if len(d) >= 10:
        phone_map[cid] = d

print(f"Total phones mapped: {len(phone_map)}")
conn.close()
