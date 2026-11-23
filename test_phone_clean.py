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

# 1. Parse existing markdown files
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
    
    # Phone regex: extract display phone before backtick and e164 in backticks
    # Format: - **WhatsApp Direto:** (21) 98935-4011 (`+5521989354011`)
    wa_match = re.search(r"- \*\*WhatsApp Direto\:\*\s*([^(]+|\([^)]+\)[^`(]+)?(?:\(`\+?(\d+)`\))?", content)
    phone_display = ""
    e164 = ""
    if wa_match:
        phone_display = (wa_match.group(1) or "").strip()
        e164 = (wa_match.group(2) or "").strip()
    
    if not e164:
        # Fallback search for wa.me in send link
        wa_link_m = re.search(r"https://wa\.me/(\d+)", content)
        if wa_link_m:
            e164 = wa_link_m.group(1)
            
    if not phone_display and e164:
        phone_display = format_phone_human(e164)
        
    url_m = re.search(r"- \*\*URL Pública Vercel\:\*\* (.+)", content)
    url_str = url_m.group(1).strip() if url_m else f"https://brag-showroom-demos.vercel.app/{slug}"
    
    # Extract ready whatsapp message
    msg_m = re.search(r"## Mensagem Pronta para WhatsApp\s+```text\s+(.*?)\s+```", content, re.DOTALL)
    msg_text = msg_m.group(1).strip() if msg_m else ""
    
    # Archetype
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
        "phone_display": phone_display,
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
sample = leads["360-sports-marina-barra"]
print("Sample cleaned phone_display:", sample["phone_display"])
print("Sample cleaned whatsapp_e164:", sample["whatsapp_e164"])
