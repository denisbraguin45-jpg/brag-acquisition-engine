import sys
sys.path.insert(0, "D:/app/brag-lead-hunter")
import re
import json
from pathlib import Path
from backend.connectors.instagram import load_legacy_instagram_leads
from backend.deduplication import normalize_slug
from backend.demo_builder import format_whatsapp_e164, format_phone_human

demos_dir = Path("D:/app/brag-lead-hunter/demos")
docs_dir = Path("D:/app/brag-lead-hunter/docs/leads")

all_demo_slugs = sorted([d.name for d in demos_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
legacy = load_legacy_instagram_leads(limit=500)
legacy_by_slug = {normalize_slug(item.get("name") or ""): item for item in legacy}

with open("D:/app/brag-lead-hunter/demos/manifest.json", "r", encoding="utf-8") as f:
    active_manifest = json.load(f)
active_slugs = {m["slug"]: m for m in active_manifest}

leads = {}

# 1. From docs_dir
for f in docs_dir.glob("*.md"):
    slug = f.stem
    content = f.read_text(encoding="utf-8")
    name_m = re.search(r"# Dossiê & Kit de Envio Direto — (.+)", content)
    name = name_m.group(1).strip() if name_m else slug
    rank_m = re.search(r"- \*\*Ranking[^*]*\:\*\* (.+)", content)
    rank_str = rank_m.group(1).strip() if rank_m else ""
    loc_m = re.search(r"- \*\*Localização\:\*\* (.+)", content)
    loc_str = loc_m.group(1).strip() if loc_m else ""
    city = loc_str.split("/")[0].strip() if "/" in loc_str else loc_str
    state = loc_str.split("/")[1].strip() if "/" in loc_str else ""
    ig_m = re.search(r"- \*\*Instagram\:\*\* \[?@?([a-zA-Z0-9._]+)\]?", content)
    ig_user = ig_m.group(1).strip() if ig_m else ""
    wa_m = re.search(r"- \*\*WhatsApp Direto\:\*\* (.+)", content)
    wa_raw = wa_m.group(1).strip() if wa_m else ""
    phone_clean = re.sub(r"[^\d]", "", wa_raw)
    phone_human = format_phone_human(phone_clean) if phone_clean else wa_raw
    e164 = format_whatsapp_e164(phone_clean) if phone_clean else ""
    url_m = re.search(r"- \*\*URL Pública Vercel\:\*\* (.+)", content)
    url_str = url_m.group(1).strip() if url_m else f"https://brag-showroom-demos.vercel.app/{slug}"
    
    # Extract ready whatsapp message
    msg_m = re.search(r"## Mensagem Pronta para WhatsApp\s+```text\s+(.*?)\s+```", content, re.DOTALL)
    msg_text = msg_m.group(1).strip() if msg_m else ""
    
    # Niche & archetype
    archetype_m = re.search(r"- \*\*Arquitetura\:\*\* (.+)", content)
    archetype = archetype_m.group(1).strip() if archetype_m else "Avantgarde Concept Store"
    
    score_m = re.search(r"- \*\*ICP Score\:\*\* (\d+)", content)
    score = int(score_m.group(1)) if score_m else 95
    
    owner = "denis"
    if "Gabriel" in rank_str or "Gabriel" in content[:400]:
        owner = "gabriel"
        
    is_active = slug in active_slugs
    
    leads[slug] = {
        "slug": slug,
        "name": name,
        "city": city,
        "state": state,
        "location": loc_str,
        "instagram_username": ig_user,
        "instagram_url": f"https://www.instagram.com/{ig_user}/" if ig_user else "",
        "phone_display": phone_human,
        "whatsapp_e164": e164,
        "demo_url": url_str,
        "whatsapp_message": msg_text,
        "archetype": archetype,
        "score": score,
        "owner": owner,
        "is_active_manifest": is_active,
        "has_demo": True
    }

# 2. Add remaining demo dirs
for slug in all_demo_slugs:
    if slug not in leads:
        leg = legacy_by_slug.get(slug, {})
        name = leg.get("name") or slug.replace("-", " ").title()
        city = leg.get("city") or "Brasil"
        state = leg.get("state") or "BR"
        ig = (leg.get("instagram_username") or "").lstrip("@")
        raw_phone = leg.get("whatsapp") or leg.get("phone") or ""
        e164 = format_whatsapp_e164(raw_phone)
        phone_h = format_phone_human(raw_phone)
        demo_u = f"https://brag-showroom-demos.vercel.app/{slug}"
        
        leads[slug] = {
            "slug": slug,
            "name": name,
            "city": city,
            "state": state,
            "location": f"{city} / {state}",
            "instagram_username": ig,
            "instagram_url": f"https://www.instagram.com/{ig}/" if ig else "",
            "phone_display": phone_h,
            "whatsapp_e164": e164,
            "demo_url": demo_u,
            "whatsapp_message": f"Olá, diretoria da *{name}*! Tudo bem?\n\nProjetamos uma demonstração funcional exclusiva do novo Showroom Digital da {name}:\n\n{demo_u}",
            "archetype": "Avantgarde Concept Store",
            "score": 90,
            "owner": "denis",
            "is_active_manifest": slug in active_slugs,
            "has_demo": True
        }

print("Total leads compiled:", len(leads))
denis_all = [l for l in leads.values() if l["owner"] == "denis"]
gabriel_all = [l for l in leads.values() if l["owner"] == "gabriel"]
denis_wa = [d for d in denis_all if d["whatsapp_e164"]]
gabriel_wa = [g for g in gabriel_all if g["whatsapp_e164"]]
print(f"Denis: {len(denis_all)} leads ({len(denis_wa)} com WhatsApp)")
print(f"Gabriel: {len(gabriel_all)} leads ({len(gabriel_wa)} com WhatsApp)")
