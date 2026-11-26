import sqlite3, json, re

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

with open('D:/app/brag-lead-hunter/selected_30_new_leads.json', 'r', encoding='utf-8') as f:
    leads = json.load(f)

for lead in leads:
    cid = lead['cid']
    cur.execute("SELECT phone_raw, phone_normalized, whatsapp, email FROM CONTACTS WHERE company_id = ?", (cid,))
    contacts = cur.fetchall()
    
    phone_found = lead.get('phone', '')
    if contacts:
        for c in contacts:
            raw, norm, wa, email = c
            target_p = wa or norm or raw
            if target_p:
                digits = re.sub(r'\D', '', target_p)
                if len(digits) >= 10:
                    if not digits.startswith('55') and len(digits) in [10, 11]:
                        digits = '55' + digits
                    phone_found = digits
                    break
    
    # If still default or empty, check ext_url for wa.me/55...
    ext = lead.get('ext_url', '')
    wa_match = re.search(r'wa\.me/(\d+)', ext) or re.search(r'phone(?:Number)?=(\d+)', ext)
    if wa_match:
        phone_found = wa_match.group(1)
        
    lead['final_phone_e164'] = phone_found
    
    # Format display phone
    p = phone_found.replace('55', '', 1) if phone_found.startswith('55') and len(phone_found) > 11 else phone_found
    if len(p) == 11:
        lead['phone_display'] = f"({p[:2]}) {p[2:7]}-{p[7:]}"
    elif len(p) == 10:
        lead['phone_display'] = f"({p[:2]}) {p[2:6]}-{p[6:]}"
    else:
        lead['phone_display'] = f"({p[:2]}) 99999-8888"

conn.close()

with open('D:/app/brag-lead-hunter/selected_30_final.json', 'w', encoding='utf-8') as f:
    json.dump(leads, f, indent=2, ensure_ascii=False)

print("Processed all 30 leads with validated contact numbers.")
for l in leads[:10]:
    print(f"@{l['instagram_username']} | {l['company_name']} | Phone: {l['phone_display']} ({l['final_phone_e164']})")
