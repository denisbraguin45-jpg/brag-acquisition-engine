import json
import sqlite3
import datetime
from pathlib import Path

BASE_DIR = Path("D:/app/brag-lead-hunter")
DEMOS_DIR = BASE_DIR / "demos"
DB_PATH = BASE_DIR / "data" / "brag_lead_hunter.db"

# 1. Carregar todas as 458 demos do banco unificado
db_demos = json.load(open(DEMOS_DIR / "database_all_demos.json", encoding="utf-8"))
print(f"Total de demonstrações unificadas: {len(db_demos)}")

# Ativar is_active_manifest = True para todas as 458 demonstrações (todas na fila de abordagem)
for d in db_demos:
    d["is_active_manifest"] = True
    d["has_demo"] = True
    if not d.get("demo_url"):
        d["demo_url"] = f"https://brag-showroom-demos.vercel.app/{d['slug']}"

(DEMOS_DIR / "database_all_demos.json").write_text(
    json.dumps(db_demos, indent=2, ensure_ascii=False), encoding="utf-8"
)

# 2. Carregar e sincronizar crm_all_leads.json com 100% das 458 demos na fila
crm_leads = json.load(open(DEMOS_DIR / "crm_all_leads.json", encoding="utf-8"))
crm_by_slug = {c["slug"]: c for c in crm_leads}

updated_crm = []
for d in db_demos:
    slug = d["slug"]
    existing = crm_by_slug.get(slug, {})
    crm_item = {
        "slug": slug,
        "name": d["name"],
        "city": d["city"],
        "state": d["state"],
        "location": d["location"],
        "instagram_username": d.get("instagram_username") or existing.get("instagram_username", ""),
        "instagram_url": d.get("instagram_url") or existing.get("instagram_url", ""),
        "phone_display": d.get("phone_display") or existing.get("phone_display", ""),
        "whatsapp_e164": d.get("whatsapp_e164") or existing.get("whatsapp_e164", ""),
        "demo_url": d.get("demo_url") or f"https://brag-showroom-demos.vercel.app/{slug}",
        "whatsapp_message": d.get("whatsapp_message") or existing.get("whatsapp_message", ""),
        "whatsapp_send_url": d.get("whatsapp_send_url") or existing.get("whatsapp_send_url", ""),
        "archetype": d.get("archetype") or existing.get("archetype", "Avantgarde Concept Store"),
        "score": d.get("score") or existing.get("score", 95),
        "owner": d.get("owner", "denis"),
        "is_active_manifest": True,
        "has_demo": True,
        "history_batch": d.get("history_batch", "Fila Ativa de Abordagem")
    }
    updated_crm.append(crm_item)

(DEMOS_DIR / "crm_all_leads.json").write_text(
    json.dumps(updated_crm, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"crm_all_leads.json sincronizado com {len(updated_crm)} leads ativos na fila de abordagem.")

# 3. Atualizar manifest.json para contemplar todas as demonstrações na esteira ativa
manifest_items = []
for idx, d in enumerate(db_demos, start=1):
    manifest_items.append({
        "rank": idx,
        "owner": d.get("owner", "denis"),
        "owner_name": d.get("owner_name", "Denis" if d.get("owner") == "denis" else "Gabriel"),
        "owner_label": d.get("owner_label", f"Fila {d.get('owner_name', 'Denis')}"),
        "partner_rank": d.get("partner_rank", idx),
        "company_id": f"comp-{d['slug']}",
        "slug": d["slug"],
        "name": d["name"],
        "short_name": d.get("short_name", d["name"]),
        "niche": d.get("niche", "P2 — Concessionárias náuticas, marinas e jet skis"),
        "vertical": "powersports",
        "archetype": d.get("archetype", "Avantgarde Concept Store"),
        "city": d.get("city", ""),
        "state": d.get("state", ""),
        "score": d.get("score", 95),
        "priority": d.get("priority", "A"),
        "instagram_username": d.get("instagram_username", ""),
        "instagram_url": d.get("instagram_url", ""),
        "instagram_bio": d.get("name", ""),
        "followers_count": 35000,
        "whatsapp_e164": d.get("whatsapp_e164", ""),
        "phone_display": d.get("phone_display", ""),
        "demo_url": d.get("demo_url", f"https://brag-showroom-demos.vercel.app/{d['slug']}"),
        "demo_path": f"/demos/{d['slug']}",
        "whatsapp_send_url": d.get("whatsapp_send_url", ""),
        "whatsapp_message": d.get("whatsapp_message", ""),
        "video_script_60s": d.get("video_script_60s", ""),
        "commercial_status": d.get("commercial_status", "demo_pronta"),
        "recommended_offer": "Showroom Digital Avantgarde com Captação WhatsApp",
        "diagnosis": "Presença digital dependente do Instagram; sem vitrine filtrável no celular."
    })

(DEMOS_DIR / "manifest.json").write_text(
    json.dumps(manifest_items, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"manifest.json atualizado com {len(manifest_items)} itens na esteira!")

# 4. Atualizar o Módulo Comercial (sales_distribution.json e SQLite SALES_LEADS)
# Carregar dados atuais de interações caso existam
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT slug, classification, stage, calls_made, calls_answered, decision_maker_contacted, demo_presented, interested, proposal_sent, negotiation_opened, deal_closed, deal_value, last_interaction_at, next_action, scheduled_callback_at, notes FROM SALES_LEADS")
existing_sales_map = {}
for row in c.fetchall():
    existing_sales_map[row[0]] = {
        "classification": row[1],
        "stage": row[2],
        "calls_made": row[3],
        "calls_answered": row[4],
        "decision_maker_contacted": row[5],
        "demo_presented": row[6],
        "interested": row[7],
        "proposal_sent": row[8],
        "negotiation_opened": row[9],
        "deal_closed": row[10],
        "deal_value": row[11],
        "last_interaction_at": row[12],
        "next_action": row[13],
        "scheduled_callback_at": row[14],
        "notes": row[15],
    }

# Distribuir as 458 demonstrações proporcionalmente entre Bruce (229) e Gabriel (229)
# Ordenar por score decrescente para manter a paridade estrita de qualidade
sorted_demos = sorted(db_demos, key=lambda x: (x.get("score", 90), x.get("priority", "B") == "A"), reverse=True)

bruce_leads = []
gabriel_leads = []

# Distribuição balanceada preservando qualquer preferência prévia de vendedor se fizer sentido,
# ou distribuindo em serpentina para manter 229 / 229 exatos e 0 duplicidades
for i, d in enumerate(sorted_demos):
    slug = d["slug"]
    state = existing_sales_map.get(slug, {})
    
    # Decisão de vendedor: alternado em serpentina
    assigned = "bruce" if (i % 2 == 0) else "gabriel"
    vendor_rank = (len(bruce_leads) + 1) if assigned == "bruce" else (len(gabriel_leads) + 1)
    
    item = {
        "slug": slug,
        "company_name": d["name"],
        "contact_name": "Diretoria Comercial",
        "segment": d.get("niche", "P2 — Concessionárias náuticas, marinas e jet skis"),
        "city": d.get("city", ""),
        "state": d.get("state", ""),
        "phone": d.get("phone_display") or d.get("whatsapp_e164", ""),
        "whatsapp_e164": d.get("whatsapp_e164", ""),
        "instagram_username": d.get("instagram_username", ""),
        "instagram_url": d.get("instagram_url", ""),
        "website_url": "",
        "demo_url": d.get("demo_url", f"https://brag-showroom-demos.vercel.app/{slug}"),
        "score": d.get("score", 95),
        "priority": d.get("priority", "A"),
        "potential_tier": "Alta" if d.get("score", 95) >= 95 else ("Média" if d.get("score", 95) >= 85 else "Baixa"),
        "assigned_vendor": assigned,
        "vendor_rank": vendor_rank,
        "classification": state.get("classification", "COLD"),
        "stage": state.get("stage", "novo_lead"),
        "calls_made": state.get("calls_made", 0),
        "calls_answered": state.get("calls_answered", 0),
        "decision_maker_contacted": state.get("decision_maker_contacted", 0),
        "demo_presented": state.get("demo_presented", 0),
        "interested": state.get("interested", 0),
        "proposal_sent": state.get("proposal_sent", 0),
        "negotiation_opened": state.get("negotiation_opened", 0),
        "deal_closed": state.get("deal_closed", 0),
        "deal_value": state.get("deal_value", 0.0),
        "last_interaction_at": state.get("last_interaction_at"),
        "next_action": state.get("next_action"),
        "scheduled_callback_at": state.get("scheduled_callback_at"),
        "notes": state.get("notes"),
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat(),
    }
    
    if assigned == "bruce":
        bruce_leads.append(item)
    else:
        gabriel_leads.append(item)

all_sales_leads = bruce_leads + gabriel_leads
print(f"Módulo Comercial distribuído: Bruce={len(bruce_leads)}, Gabriel={len(gabriel_leads)}, Total={len(all_sales_leads)}")

# Salvar em sales_distribution_400.json (renovado com todas as 458)
(DEMOS_DIR / "sales_distribution_400.json").write_text(
    json.dumps(all_sales_leads, indent=2, ensure_ascii=False), encoding="utf-8"
)

# Atualizar banco de dados SQLite SALES_LEADS
c.execute("DELETE FROM SALES_LEADS")
for item in all_sales_leads:
    c.execute(
        """
        INSERT INTO SALES_LEADS (
            slug, company_name, contact_name, segment, city, state, phone, whatsapp_e164,
            instagram_username, instagram_url, website_url, demo_url, score, priority,
            potential_tier, assigned_vendor, vendor_rank, classification, stage,
            calls_made, calls_answered, decision_maker_contacted, demo_presented,
            interested, proposal_sent, negotiation_opened, deal_closed, deal_value,
            last_interaction_at, next_action, scheduled_callback_at, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["slug"], item["company_name"], item["contact_name"], item["segment"],
            item["city"], item["state"], item["phone"], item["whatsapp_e164"],
            item["instagram_username"], item["instagram_url"], item["website_url"],
            item["demo_url"], item["score"], item["priority"], item["potential_tier"],
            item["assigned_vendor"], item["vendor_rank"], item["classification"],
            item["stage"], item["calls_made"], item["calls_answered"],
            item["decision_maker_contacted"], item["demo_presented"], item["interested"],
            item["proposal_sent"], item["negotiation_opened"], item["deal_closed"],
            item["deal_value"], item["last_interaction_at"], item["next_action"],
            item["scheduled_callback_at"], item["notes"], item["created_at"], item["updated_at"]
        )
    )

# Atualizar registro de distribuição na tabela SALES_DISTRIBUTION
c.execute("DELETE FROM SALES_DISTRIBUTION")
c.execute(
    """
    INSERT INTO SALES_DISTRIBUTION (
        distributed_at, distributed_by, total_leads, bruce_leads_count,
        gabriel_leads_count, criteria
    ) VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        datetime.datetime.now().isoformat(),
        "Admin BRAG",
        len(all_sales_leads),
        len(bruce_leads),
        len(gabriel_leads),
        json.dumps({
            "total": len(all_sales_leads),
            "bruce": len(bruce_leads),
            "gabriel": len(gabriel_leads),
            "mode": "Integracao total das 458 demos na fila de abordagem"
        })
    )
)
conn.commit()
conn.close()
print("Banco SQLite atualizado com 100% das 458 demonstrações integradas à esteira comercial!")
