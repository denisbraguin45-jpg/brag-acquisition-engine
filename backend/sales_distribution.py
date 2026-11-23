import json
import sqlite3
import datetime
from pathlib import Path
from backend.sales_db import DB_PATH, DEMOS_DIR, init_sales_tables

DISTRIBUTION_JSON_PATH = DEMOS_DIR / "sales_distribution_400.json"

def perform_distribution(force: bool = False):
    conn = sqlite3.connect(DB_PATH)
    init_sales_tables(conn)
    c = conn.cursor()

    c.execute("SELECT count(*) FROM SALES_LEADS")
    existing_count = c.fetchone()[0]

    if existing_count >= 400 and not force:
        print(f"Distribution already present with {existing_count} leads. Reading from database...")
        c.execute("SELECT * FROM SALES_LEADS ORDER BY assigned_vendor, vendor_rank")
        # Generate JSON cache
        cols = [col[0] for col in c.description]
        rows = [dict(zip(cols, r)) for r in c.fetchall()]
        DISTRIBUTION_JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        conn.close()
        return rows

    # Load 428 records from database_all_demos.json
    db_demos_path = DEMOS_DIR / "database_all_demos.json"
    with open(db_demos_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Deduplicate strictly by slug, name, and phone
    seen_slugs = set()
    seen_phones = set()
    unique_candidates = []

    # Sort candidates by ICP Score descending so the top 400 highest commercial potential are picked
    def sort_key(r):
        prio_order = 0 if r.get("priority") == "A" else 1
        return (-r.get("score", 0), prio_order, r.get("name", ""))

    sorted_records = sorted(records, key=sort_key)

    for r in sorted_records:
        slug = r.get("slug")
        phone = r.get("whatsapp_e164") or r.get("phone_display")
        if not slug or slug in seen_slugs:
            continue
        # If phone is already in, skip duplicate contact
        if phone and phone in seen_phones:
            continue
        seen_slugs.add(slug)
        if phone:
            seen_phones.add(phone)
        unique_candidates.append(r)

    print(f"Total unique candidates identified: {len(unique_candidates)}")
    assert len(unique_candidates) >= 400, f"Expected at least 400 unique candidates, got {len(unique_candidates)}"

    top_400 = unique_candidates[:400]

    # Proportional classification by commercial potential tier
    # High: score >= 95, Medium: 85 <= score < 95, Low: score < 85
    high = [r for r in top_400 if r.get("score", 0) >= 95]
    med = [r for r in top_400 if 85 <= r.get("score", 0) < 95]
    low = [r for r in top_400 if r.get("score", 0) < 85]

    bruce_leads = []
    gabriel_leads = []

    # Alternating serpentine allocation per tier to ensure exact 50/50 split across all tiers
    for tier, tier_name in [(high, "high"), (med, "medium"), (low, "low")]:
        for i, lead in enumerate(tier):
            lead["potential_tier"] = tier_name
            if (len(bruce_leads) <= len(gabriel_leads) and len(bruce_leads) < 200) or len(gabriel_leads) == 200:
                lead["assigned_vendor"] = "bruce"
                bruce_leads.append(lead)
            else:
                lead["assigned_vendor"] = "gabriel"
                gabriel_leads.append(lead)

    assert len(bruce_leads) == 200, f"Bruce got {len(bruce_leads)}, expected 200"
    assert len(gabriel_leads) == 200, f"Gabriel got {len(gabriel_leads)}, expected 200"

    # Sort each vendor's portfolio by score descending and assign vendor_rank 1..200
    bruce_leads.sort(key=sort_key)
    gabriel_leads.sort(key=sort_key)

    now_iso = datetime.datetime.now().isoformat()

    c.execute("DELETE FROM SALES_LEADS")
    c.execute("DELETE FROM SALES_DISTRIBUTION")

    # Insert distribution record
    c.execute("""
    INSERT INTO SALES_DISTRIBUTION (distributed_at, distributed_by, total_leads, bruce_leads_count, gabriel_leads_count, criteria)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        now_iso,
        "BRAG Sales Operation Engine",
        400,
        200,
        200,
        "Serpentine Proportional Allocation across High (>=95), Medium (85-94) and Low (<85) ICP Scores"
    ))

    all_distributed = []

    for rank, lead in enumerate(bruce_leads, 1):
        lead_record = {
            "slug": lead["slug"],
            "company_name": lead["name"],
            "contact_name": lead.get("short_name") or lead["name"].split("|")[0].strip(),
            "segment": lead.get("niche") or "P1 — Concessionárias de luxo & supercarros",
            "city": lead.get("city") or "Brasil",
            "state": lead.get("state") or "BR",
            "phone": lead.get("phone_display") or lead.get("whatsapp_e164") or "",
            "whatsapp_e164": lead.get("whatsapp_e164") or "",
            "instagram_username": lead.get("instagram_username") or "",
            "instagram_url": lead.get("instagram_url") or "",
            "website_url": lead.get("website_url") or "",
            "demo_url": lead.get("demo_url") or f"https://brag-showroom-demos.vercel.app/{lead['slug']}",
            "score": lead.get("score") or 90,
            "priority": lead.get("priority") or "A",
            "potential_tier": lead["potential_tier"],
            "assigned_vendor": "bruce",
            "vendor_rank": rank,
            "classification": "COLD",
            "stage": "novo_lead",
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
            "next_action": "Realizar primeira ligação com Script 1",
            "scheduled_callback_at": None,
            "notes": None,
            "created_at": now_iso,
            "updated_at": now_iso
        }
        all_distributed.append(lead_record)
        c.execute("""
        INSERT INTO SALES_LEADS (
            slug, company_name, contact_name, segment, city, state, phone, whatsapp_e164,
            instagram_username, instagram_url, website_url, demo_url, score, priority,
            potential_tier, assigned_vendor, vendor_rank, classification, stage,
            calls_made, calls_answered, decision_maker_contacted, demo_presented,
            interested, proposal_sent, negotiation_opened, deal_closed, deal_value,
            last_interaction_at, next_action, scheduled_callback_at, notes,
            created_at, updated_at
        ) VALUES (
            :slug, :company_name, :contact_name, :segment, :city, :state, :phone, :whatsapp_e164,
            :instagram_username, :instagram_url, :website_url, :demo_url, :score, :priority,
            :potential_tier, :assigned_vendor, :vendor_rank, :classification, :stage,
            :calls_made, :calls_answered, :decision_maker_contacted, :demo_presented,
            :interested, :proposal_sent, :negotiation_opened, :deal_closed, :deal_value,
            :last_interaction_at, :next_action, :scheduled_callback_at, :notes,
            :created_at, :updated_at
        )
        """, lead_record)

    for rank, lead in enumerate(gabriel_leads, 1):
        lead_record = {
            "slug": lead["slug"],
            "company_name": lead["name"],
            "contact_name": lead.get("short_name") or lead["name"].split("|")[0].strip(),
            "segment": lead.get("niche") or "P1 — Concessionárias de luxo & supercarros",
            "city": lead.get("city") or "Brasil",
            "state": lead.get("state") or "BR",
            "phone": lead.get("phone_display") or lead.get("whatsapp_e164") or "",
            "whatsapp_e164": lead.get("whatsapp_e164") or "",
            "instagram_username": lead.get("instagram_username") or "",
            "instagram_url": lead.get("instagram_url") or "",
            "website_url": lead.get("website_url") or "",
            "demo_url": lead.get("demo_url") or f"https://brag-showroom-demos.vercel.app/{lead['slug']}",
            "score": lead.get("score") or 90,
            "priority": lead.get("priority") or "A",
            "potential_tier": lead["potential_tier"],
            "assigned_vendor": "gabriel",
            "vendor_rank": rank,
            "classification": "COLD",
            "stage": "novo_lead",
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
            "next_action": "Realizar primeira ligação com Script 1",
            "scheduled_callback_at": None,
            "notes": None,
            "created_at": now_iso,
            "updated_at": now_iso
        }
        all_distributed.append(lead_record)
        c.execute("""
        INSERT INTO SALES_LEADS (
            slug, company_name, contact_name, segment, city, state, phone, whatsapp_e164,
            instagram_username, instagram_url, website_url, demo_url, score, priority,
            potential_tier, assigned_vendor, vendor_rank, classification, stage,
            calls_made, calls_answered, decision_maker_contacted, demo_presented,
            interested, proposal_sent, negotiation_opened, deal_closed, deal_value,
            last_interaction_at, next_action, scheduled_callback_at, notes,
            created_at, updated_at
        ) VALUES (
            :slug, :company_name, :contact_name, :segment, :city, :state, :phone, :whatsapp_e164,
            :instagram_username, :instagram_url, :website_url, :demo_url, :score, :priority,
            :potential_tier, :assigned_vendor, :vendor_rank, :classification, :stage,
            :calls_made, :calls_answered, :decision_maker_contacted, :demo_presented,
            :interested, :proposal_sent, :negotiation_opened, :deal_closed, :deal_value,
            :last_interaction_at, :next_action, :scheduled_callback_at, :notes,
            :created_at, :updated_at
        )
        """, lead_record)

    conn.commit()
    conn.close()

    DISTRIBUTION_JSON_PATH.write_text(json.dumps(all_distributed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Distribution of 400 leads committed successfully to SQLite and cached at {DISTRIBUTION_JSON_PATH}!")
    return all_distributed

if __name__ == "__main__":
    perform_distribution(force=True)
