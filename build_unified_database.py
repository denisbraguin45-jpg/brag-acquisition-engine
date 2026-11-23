import sys
sys.path.insert(0, "D:/app/brag-lead-hunter")
import json
import urllib.parse
from pathlib import Path
from backend.demo_builder import format_phone_human, format_whatsapp_e164

demos_dir = Path("D:/app/brag-lead-hunter/demos")
with open(demos_dir / "crm_all_leads.json", "r", encoding="utf-8") as f:
    crm_leads = json.load(f)

with open(demos_dir / "manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

manifest_by_slug = {m["slug"]: m for m in manifest}

unified_database = []

# Separate into Denis and Gabriel
denis_leads = [l for l in crm_leads if l.get("owner") == "denis"]
gabriel_leads = [l for l in crm_leads if l.get("owner") == "gabriel"]

# Order so active manifest leads come first, then history
def sort_key(l):
    is_act = 0 if l.get("is_active_manifest") else 1
    return (is_act, l.get("name", "").lower())

denis_leads.sort(key=sort_key)
gabriel_leads.sort(key=sort_key)

# Assign ranks
for idx, l in enumerate(denis_leads, 1):
    slug = l["slug"]
    man = manifest_by_slug.get(slug, {})
    
    # Fill in enriched fields
    short_name = l["name"].split("|")[0].split(" - ")[0].strip()
    e164 = l.get("whatsapp_e164") or format_whatsapp_e164(l.get("phone_display", ""))
    phone_h = l.get("phone_display") or format_phone_human(e164)
    demo_u = l.get("demo_url") or f"https://brag-showroom-demos.vercel.app/{slug}"
    msg = l.get("whatsapp_message") or man.get("whatsapp_message") or ""
    if not msg:
        msg = (
            f"Olá, diretoria da *{short_name}*! Tudo bem?\n\n"
            f"Projetamos e colocamos no ar uma demonstração funcional exclusiva do novo Showroom Digital da {short_name}:\n\n"
            f"{demo_u}\n\n"
            f"Podem abrir direto no celular para testar a experiência."
        )
    send_u = l.get("whatsapp_send_url") or (f"https://wa.me/{e164}?text={urllib.parse.quote(msg)}" if e164 else "")
    
    script_60s = man.get("video_script_60s") or f"""# Roteiro de Vídeo Executivo (45 a 60s) — {l['name']}
> Responsável pelo Disparo: Denis (Fila Denis · #{idx:03d})
> Link Público Vercel: {demo_u}

## [00:00 - 00:15] Abertura & Reconhecimento
"Olá pessoal da {short_name}, aqui é o Denis da BRAG. Estávamos acompanhando a operação de vocês..."

## [00:15 - 00:45] Apresentação do Showroom
"Desenhamos uma demonstração funcional sob medida para a {short_name}: {demo_u}. Filtro instantâneo no mobile e contato direto no WhatsApp."

## [00:45 - 00:60] Fechamento
"Link para testar direto no celular. Se fizer sentido ativarmos essa estrutura oficial para a {short_name}, fico à disposição."
"""

    record = {
        "rank": idx,
        "partner_rank": idx,
        "owner": "denis",
        "owner_name": "Denis",
        "owner_label": "Fila Denis",
        "slug": slug,
        "name": l["name"],
        "short_name": short_name,
        "city": l.get("city") or "Brasil",
        "state": l.get("state") or "BR",
        "location": l.get("location") or f"{l.get('city', '')} / {l.get('state', '')}",
        "niche": l.get("niche") or man.get("niche") or "P4 — Náutica premium & concessionárias",
        "archetype": l.get("archetype") or man.get("archetype") or "Avantgarde Concept Store",
        "score": l.get("score") or 96,
        "priority": "A" if (l.get("score") or 90) >= 85 else "B",
        "instagram_username": l.get("instagram_username") or "",
        "instagram_url": l.get("instagram_url") or (f"https://www.instagram.com/{l.get('instagram_username')}/" if l.get("instagram_username") else ""),
        "whatsapp_e164": e164,
        "phone_display": phone_h,
        "demo_url": demo_u,
        "demo_path": f"/demos/{slug}",
        "whatsapp_send_url": send_u,
        "whatsapp_message": msg,
        "video_script_60s": script_60s,
        "commercial_status": "demo_pronta",
        "is_active_manifest": l.get("is_active_manifest", False),
        "history_batch": l.get("history_batch", "Denis Carteira de Demos"),
        "has_demo": True
    }
    unified_database.append(record)

for idx, l in enumerate(gabriel_leads, 1):
    slug = l["slug"]
    man = manifest_by_slug.get(slug, {})
    
    short_name = l["name"].split("|")[0].split(" - ")[0].strip()
    e164 = l.get("whatsapp_e164") or format_whatsapp_e164(l.get("phone_display", ""))
    phone_h = l.get("phone_display") or format_phone_human(e164)
    demo_u = l.get("demo_url") or f"https://brag-showroom-demos.vercel.app/{slug}"
    msg = l.get("whatsapp_message") or man.get("whatsapp_message") or ""
    if not msg:
        msg = (
            f"Olá, diretoria da *{short_name}*! Tudo bem?\n\n"
            f"Projetamos e colocamos no ar uma demonstração funcional exclusiva do novo Showroom Digital da {short_name}:\n\n"
            f"{demo_u}\n\n"
            f"Podem abrir direto no celular para testar a experiência."
        )
    send_u = l.get("whatsapp_send_url") or (f"https://wa.me/{e164}?text={urllib.parse.quote(msg)}" if e164 else "")
    
    script_60s = man.get("video_script_60s") or f"""# Roteiro de Vídeo Executivo (45 a 60s) — {l['name']}
> Responsável pelo Disparo: Gabriel (Fila Gabriel · #{idx:03d})
> Link Público Vercel: {demo_u}

## [00:00 - 00:15] Abertura & Reconhecimento
"Olá pessoal da {short_name}, aqui é o Gabriel da BRAG..."

## [00:15 - 00:45] Apresentação do Showroom
"Desenhamos uma demonstração funcional sob medida para a {short_name}: {demo_u}."

## [00:45 - 00:60] Fechamento
"Link para testar direto no celular. Se fizer sentido ativarmos essa estrutura oficial para a {short_name}, fico à disposição."
"""

    record = {
        "rank": idx,
        "partner_rank": idx,
        "owner": "gabriel",
        "owner_name": "Gabriel",
        "owner_label": "Fila Gabriel",
        "slug": slug,
        "name": l["name"],
        "short_name": short_name,
        "city": l.get("city") or "Brasil",
        "state": l.get("state") or "BR",
        "location": l.get("location") or f"{l.get('city', '')} / {l.get('state', '')}",
        "niche": l.get("niche") or man.get("niche") or "P1 — Revendas premium e blindados",
        "archetype": l.get("archetype") or man.get("archetype") or "Campello Racing Portugal",
        "score": l.get("score") or 96,
        "priority": "A" if (l.get("score") or 90) >= 85 else "B",
        "instagram_username": l.get("instagram_username") or "",
        "instagram_url": l.get("instagram_url") or (f"https://www.instagram.com/{l.get('instagram_username')}/" if l.get("instagram_username") else ""),
        "whatsapp_e164": e164,
        "phone_display": phone_h,
        "demo_url": demo_u,
        "demo_path": f"/demos/{slug}",
        "whatsapp_send_url": send_u,
        "whatsapp_message": msg,
        "video_script_60s": script_60s,
        "commercial_status": "demo_pronta",
        "is_active_manifest": l.get("is_active_manifest", False),
        "history_batch": l.get("history_batch", "Gabriel Carteira de Demos"),
        "has_demo": True
    }
    unified_database.append(record)

print(f"Unified database total: {len(unified_database)}")
# Write to demos/database_all_demos.json and update manifest.json
output_file = demos_dir / "database_all_demos.json"
output_file.write_text(json.dumps(unified_database, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {output_file} successfully!")
