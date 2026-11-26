import json, sqlite3
from pathlib import Path

BASE = Path("D:/app/brag-lead-hunter")

# Load existing sales distribution
sales_path = BASE / "demos/sales_distribution_400.json"
with open(sales_path, "r", encoding="utf-8") as f:
    sales_list = json.load(f)

# Load 30 new demos
with open(BASE / "new_30_vetted_demos.json", "r", encoding="utf-8") as f:
    new_demos = json.load(f)

print(f"Current sales leads: {len(sales_list)}")
print(f"Adding new vetted demos: {len(new_demos)}")

# Format new leads for sales_distribution_400.json
existing_slugs = {s["slug"] for s in sales_list}
added_count = 0

for lead in new_demos:
    if lead["slug"] in existing_slugs:
        continue
    
    # Matching sales_distribution schema
    sales_record = {
        "slug": lead["slug"],
        "company_name": lead["company_name"],
        "contact_name": lead["contact_name"],
        "segment": lead["segment"],
        "city": lead["city"],
        "state": lead["state"],
        "phone": lead["phone"],
        "whatsapp_e164": lead["whatsapp_e164"],
        "instagram_username": lead["instagram_username"],
        "instagram_handle": f"@{lead['instagram_username']}",
        "instagram_url": lead["instagram_url"],
        "website_url": "",
        "demo_url": lead["demo_url"],
        "score": lead["score"],
        "priority": lead["priority"],
        "potential_tier": lead["potential_tier"],
        "assigned_vendor": lead["assigned_vendor"],
        "vendor_rank": lead["vendor_rank"],
        "classification": lead["classification"],
        "stage": lead["stage"],
        "calls_made": 0,
        "calls_answered": 0,
        "decision_maker_contacted": 0,
        "demo_presented": 0,
        "interested": 0,
        "proposal_sent": 0,
        "negotiation_opened": 0,
        "deal_closed": 0,
        "deal_value": 0.0,
        "last_interaction_at": None,
        "next_action": lead["next_action"],
        "scheduled_callback_at": None,
        "notes": lead["notes"],
        "whatsapp_message": lead["whatsapp_message"],
        "whatsapp_send_url": lead["whatsapp_send_url"],
        "meeting_scheduled_at": None,
        "meeting_notes": "",
        "meeting_link": ""
    }
    sales_list.append(sales_record)
    added_count += 1

print(f"Added {added_count} records. New total: {len(sales_list)}")

# Save updated sales_distribution_400.json
with open(sales_path, "w", encoding="utf-8") as f:
    json.dump(sales_list, f, indent=2, ensure_ascii=False)

# Update database_all_demos.json if exists
all_demos_path = BASE / "demos/database_all_demos.json"
if all_demos_path.exists():
    with open(all_demos_path, "r", encoding="utf-8") as f:
        all_demos = json.load(f)
    existing_all_slugs = {d.get("slug") for d in all_demos}
    for lead in new_demos:
        if lead["slug"] not in existing_all_slugs:
            all_demos.append(lead)
    with open(all_demos_path, "w", encoding="utf-8") as f:
        json.dump(all_demos, f, indent=2, ensure_ascii=False)
    print(f"Updated database_all_demos.json. Total: {len(all_demos)}")

# Update SQLite SALES_LEADS
conn = sqlite3.connect(BASE / "data/brag_lead_hunter.db")
cur = conn.cursor()

for lead in new_demos:
    cur.execute("SELECT slug FROM SALES_LEADS WHERE slug = ?", (lead["slug"],))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO SALES_LEADS (
                slug, company_name, contact_name, segment, city, state,
                phone, whatsapp_e164, instagram_username, instagram_url,
                website_url, demo_url, score, priority, potential_tier,
                assigned_vendor, vendor_rank, classification, stage,
                calls_made, calls_answered, decision_maker_contacted,
                demo_presented, interested, proposal_sent, negotiation_opened,
                deal_closed, deal_value, last_interaction_at, next_action,
                scheduled_callback_at, notes, created_at, updated_at,
                whatsapp_message, whatsapp_send_url, meeting_scheduled_at,
                meeting_notes, meeting_link
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, datetime('now'), datetime('now'),
                ?, ?, ?,
                ?, ?
            )
        """, (
            lead["slug"], lead["company_name"], lead["contact_name"], lead["segment"], lead["city"], lead["state"],
            lead["phone"], lead["whatsapp_e164"], lead["instagram_username"], lead["instagram_url"],
            lead["website_url"], lead["demo_url"], lead["score"], lead["priority"], lead["potential_tier"],
            lead["assigned_vendor"], lead["vendor_rank"], lead["classification"], lead["stage"],
            lead["calls_made"], lead["calls_answered"], lead["decision_maker_contacted"],
            lead["demo_presented"], lead["interested"], lead["proposal_sent"], lead["negotiation_opened"],
            lead["deal_closed"], lead["deal_value"], lead["last_interaction_at"], lead["next_action"],
            lead["scheduled_callback_at"], lead["notes"],
            lead["whatsapp_message"], lead["whatsapp_send_url"], None,
            "", ""
        ))

conn.commit()
cur.execute("SELECT count(*) FROM SALES_LEADS")
db_count = cur.fetchone()[0]
print(f"Total rows in SALES_LEADS SQLite: {db_count}")
conn.close()

print("Integração concluída com sucesso!")
