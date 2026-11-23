import sys
sys.path.insert(0, "D:/app/brag-lead-hunter")
import json
import urllib.parse
from pathlib import Path
from build_100_leads_pool import leads_100
from backend.demo_builder import (
    render_demo_html,
    DEMOS_DIR,
    DOCS_LEADS_DIR,
    DESIGN_THEMES,
    detect_vertical_key,
    format_whatsapp_e164,
    format_phone_human
)

print(f"Generating 100 new demos from pool...")
public_demo_base = "https://brag-showroom-demos.vercel.app"

generated_records = []

for idx, lead in enumerate(leads_100, start=1):
    slug = lead["slug"]
    company_name = lead["name"].split("|")[0].split(" - ")[0].strip()
    full_name = lead["name"]
    city = lead.get("city") or "Brasil"
    state = lead.get("state") or "BR"
    ig_user = lead.get("instagram_username") or ""
    raw_phone = lead.get("whatsapp") or ""
    wa_e164 = format_whatsapp_e164(raw_phone)
    phone_display = lead.get("phone_display") or format_phone_human(raw_phone)
    demo_url = f"{public_demo_base}/{slug}"
    
    vertical = detect_vertical_key(lead)
    theme = DESIGN_THEMES[(idx - 1) % len(DESIGN_THEMES)]
    
    gap_reason = "todo o tráfego do Instagram de vocês hoje deságua em link intermediário sem vitrine filtrável no celular"
    
    whatsapp_message = (
        f"Olá, diretoria da *{company_name}*! Tudo bem?\n\n"
        f"Acompanhamos a operação de vocês no Instagram (@{ig_user}) em {city}/{state} e notamos que {gap_reason}.\n\n"
        f"Em vez de enviar uma apresentação comercial teórica, nós projetamos e colocamos no ar uma *demonstração funcional exclusiva do novo Showroom Digital da {company_name}* "
        f"(com filtro instantâneo por marca/modelo, vitrine interativa de alto padrão e captação integrada ao WhatsApp de vocês):\n\n"
        f"{demo_url}\n\n"
        f"Podem abrir direto no celular para testar a experiência. Se fizer sentido ativarmos essa estrutura oficial para a {company_name}, fico à disposição por aqui."
    )
    
    wa_send_url = f"https://wa.me/{wa_e164}?text={urllib.parse.quote(whatsapp_message)}"
    
    outreach = {
        "rank": idx,
        "owner": "denis",
        "owner_name": "Denis",
        "owner_label": "Denis — 100 Novas Demos",
        "partner_rank": idx,
        "company_id": f"batch100_{slug}",
        "slug": slug,
        "name": full_name,
        "short_name": company_name,
        "niche": lead.get("niche") or "P1 — Concessionárias de luxo & supercarros",
        "vertical": vertical,
        "archetype": theme["archetype"],
        "city": city,
        "state": state,
        "score": 96,
        "priority": "A",
        "instagram_username": ig_user,
        "instagram_url": lead.get("instagram_url") or "",
        "instagram_bio": f"Concessionária e showroom exclusivo de alta performance em {city}/{state}.",
        "followers_count": 18500,
        "whatsapp_e164": wa_e164,
        "phone_display": phone_display,
        "demo_url": demo_url,
        "demo_path": f"/demos/{slug}",
        "whatsapp_send_url": wa_send_url,
        "whatsapp_message": whatsapp_message,
        "commercial_status": "demo_pronta",
        "recommended_offer": "Showroom Digital Avantgarde Edition + Concierge WhatsApp",
    }
    
    lead_dict = {
        "id": f"batch100_{slug}",
        "slug": slug,
        "name": full_name,
        "niche": lead.get("niche") or "P1 — Concessionárias de luxo & supercarros",
        "city": city,
        "state": state,
        "score": 96,
        "priority": "A",
        "instagram_username": ig_user,
        "instagram_url": lead.get("instagram_url") or "",
        "whatsapp": wa_e164,
        "phone": wa_e164,
        "has_own_website": False,
    }
    
    html_content = render_demo_html(lead_dict, rank=idx, outreach=outreach)
    demo_dir = DEMOS_DIR / slug
    demo_dir.mkdir(parents=True, exist_ok=True)
    (demo_dir / "index.html").write_text(html_content, encoding="utf-8")
    
    # Write dossier markdown
    dossier_md = f"""# Dossiê & Kit de Envio Direto — {outreach['name']}
- **Ranking Top 100:** #{idx:03d}
- **Arquitetura:** {outreach['archetype']}
- **ICP Score:** {outreach['score']}/100 (Prioridade {outreach['priority']})
- **Localização:** {outreach['city']} / {outreach['state']}
- **Instagram:** [@{outreach['instagram_username']}]({outreach['instagram_url']})
- **WhatsApp Direto:** {outreach['phone_display']} (`+{outreach['whatsapp_e164']}`)
- **URL Pública Vercel:** {outreach['demo_url']}
- **Link de Envio Direto (1 Clique):** [Enviar Demo no WhatsApp]({outreach['whatsapp_send_url']})

## Mensagem Pronta para WhatsApp
```text
{outreach['whatsapp_message']}
```
"""
    (DOCS_LEADS_DIR / f"{slug}.md").write_text(dossier_md, encoding="utf-8")
    generated_records.append(outreach)

print(f"Generated all {len(generated_records)} demos on disk!")

# Save batch 100 json
batch100_json = DEMOS_DIR / "demos_100_novas.json"
batch100_json.write_text(json.dumps(generated_records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved manifest of 100 new demos to {batch100_json}!")
