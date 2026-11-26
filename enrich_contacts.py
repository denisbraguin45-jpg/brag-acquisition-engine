import sqlite3, json

conn = sqlite3.connect('D:/app/brag-lead-hunter/data/brag_lead_hunter.db')
cur = conn.cursor()

with open('D:/app/brag-lead-hunter/selected_30_new_leads.json', 'r', encoding='utf-8') as f:
    leads = json.load(f)

for lead in leads:
    cid = lead['cid']
    cur.execute("SELECT name, phone, mobile, whatsapp, email, role FROM CONTACTS WHERE company_id = ?", (cid,))
    contacts = cur.fetchall()
    cur.execute("SELECT address, phone, maps_url FROM COMPANIES WHERE id = ?", (cid,))
    comp_row = cur.fetchone()
    lead['db_contacts'] = contacts
    lead['db_company'] = comp_row

conn.close()

with open('D:/app/brag-lead-hunter/selected_30_with_contacts.json', 'w', encoding='utf-8') as f:
    json.dump(leads, f, indent=2, ensure_ascii=False)

print("Checked contacts for all 30 leads.")
for l in leads[:5]:
    print(l['company_name'], '| Contacts:', l['db_contacts'], '| Comp:', l['db_company'])
