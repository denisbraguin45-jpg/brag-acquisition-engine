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
print("Total demo slugs on disk:", len(all_demo_slugs))

legacy = load_legacy_instagram_leads(limit=500)
legacy_by_slug = {normalize_slug(item.get("name") or ""): item for item in legacy}

all_leads_dict = {}

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
    
    ig_m = re.search(r"- \*\*Instagram\:\*\* \[?@?([a-zA-Z0-9._]+)\]?", content)
    ig_user = ig_m.group(1).strip() if ig_m else ""
    
    wa_m = re.search(r"- \*\*WhatsApp Direto\:\*\* (.+)", content)
    wa_raw = wa_m.group(1).strip() if wa_m else ""
    
    # Extract clean digits from wa_raw
    phone_clean = re.sub(r"[^\d]", "", wa_raw)
    phone_human = format_phone_human(phone_clean) if phone_clean else wa_raw
    e164 = format_whatsapp_e164(phone_clean) if phone_clean else ""
    
    url_m = re.search(r"- \*\*URL Pública Vercel\:\*\* (.+)", content)
    url_str = url_m.group(1).strip() if url_m else f"https://brag-showroom-demos.vercel.app/{slug}"
    
    send_m = re.search(r"\[Enviar Demo no WhatsApp\]\((https://wa\.me/[^\)]+)\)", content)
    send_url = send_m.group(1).strip() if send_m else (f"https://wa.me/{e164}" if e164 else "")
    
    owner = "denis"
    if "Gabriel" in rank_str or "Gabriel" in content[:400]:
        owner = "gabriel"

    all_leads_dict[slug] = {
        "slug": slug,
        "name": name,
        "location": loc_str,
        "instagram": ig_user,
        "phone": phone_human,
        "whatsapp_e164": e164,
        "demo_url": url_str,
        "whatsapp_send_url": send_url,
        "owner": owner,
        "source": "docs_dossier"
    }

# 2. Add slugs from demos without markdown dossiers
for slug in all_demo_slugs:
    if slug not in all_leads_dict:
        leg = legacy_by_slug.get(slug, {})
        name = leg.get("name") or slug.replace("-", " ").title()
        city = leg.get("city") or "Brasil"
        state = leg.get("state") or "BR"
        ig = (leg.get("instagram_username") or "").lstrip("@")
        raw_phone = leg.get("whatsapp") or leg.get("phone") or ""
        e164 = format_whatsapp_e164(raw_phone)
        phone_h = format_phone_human(raw_phone)
        demo_u = f"https://brag-showroom-demos.vercel.app/{slug}"
        send_u = f"https://wa.me/{e164}" if e164 else ""
        
        all_leads_dict[slug] = {
            "slug": slug,
            "name": name,
            "location": f"{city} / {state}",
            "instagram": ig,
            "phone": phone_h,
            "whatsapp_e164": e164,
            "demo_url": demo_u,
            "whatsapp_send_url": send_u,
            "owner": "denis",
            "source": "legacy_lote1"
        }

print("Total unified leads with demos:", len(all_leads_dict))
denis_all = [l for l in all_leads_dict.values() if l["owner"] == "denis"]
gabriel_all = [l for l in all_leads_dict.values() if l["owner"] == "gabriel"]
print("Denis leads count:", len(denis_all))
print("Gabriel leads count:", len(gabriel_all))
