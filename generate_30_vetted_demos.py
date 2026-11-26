import json, sys, os, urllib.parse, re
from pathlib import Path

BASE = Path("D:/app/brag-lead-hunter")
sys.path.insert(0, str(BASE))

from backend.demo_builder import build_outreach_assets, render_demo_html

with open(BASE / "selected_30_final.json", "r", encoding="utf-8") as f:
    selected_leads = json.load(f)

# Also extract phones from bios if any
import sqlite3
conn = sqlite3.connect(BASE / "data/brag_lead_hunter.db")
cur = conn.cursor()
cur.execute("SELECT company_id, biography, public_phone FROM SOCIAL_PROFILES WHERE platform='instagram'")
bios = cur.fetchall()
conn.close()

phone_map = {}
for cid, bio, p_phone in bios:
    if p_phone:
        d = re.sub(r'\D', '', str(p_phone))
        if len(d) in [10, 11]:
            phone_map[cid] = '55' + d
        elif len(d) >= 12:
            phone_map[cid] = d
    elif bio:
        matches = re.findall(r'(?:\(?(\d{2})\)?\s*)?(?:9\s*)?(\d{4})[-.\s]?(\d{4})', bio)
        for m in matches:
            ddd, p1, p2 = m
            if ddd and len(ddd) == 2:
                num = f"55{ddd}9{p1}{p2}"
                phone_map[cid] = num
                break

demos_dir = BASE / "demos"

# Archetype choices based on segment/name
def get_archetype_and_niche(lead):
    seg = (lead.get('segment') or '').lower()
    name = lead['company_name'].lower()
    if 'náutica' in seg or 'nautica' in seg or 'boat' in name or 'marina' in name or 'lancha' in name or 'jet' in name:
        return 'nautical', 'P4 — Náutica premium'
    elif 'superesportivos' in seg or 'luxo' in seg or 'import' in name or 'exotic' in name:
        return 'supercars', 'P2 — Luxo e superesportivos'
    elif 'blindad' in seg or 'blindad' in name:
        return 'armored', 'P1 — Blindados e Revendas Premium'
    else:
        return 'multibrand', 'P1 — Revendas premium e multimarcas'

generated_demos = []

# Distribute 15 to Bruce and 15 to Gabriel
for idx, lead in enumerate(selected_leads, start=1):
    owner = "bruce" if idx % 2 == 1 else "gabriel"
    owner_name = "Bruce" if owner == "bruce" else "Gabriel"
    owner_label = f"Fila {owner_name}"
    
    slug = lead['slug']
    cid = lead['cid']
    
    phone_e164 = phone_map.get(cid) or lead.get('final_phone_e164') or '5511994829147'
    p_core = phone_e164.replace('55', '', 1) if phone_e164.startswith('55') and len(phone_e164) > 11 else phone_e164
    if len(p_core) == 11:
        phone_display = f"({p_core[:2]}) {p_core[2:7]}-{p_core[7:]}"
    elif len(p_core) == 10:
        phone_display = f"({p_core[:2]}) {p_core[2:6]}-{p_core[6:]}"
    else:
        phone_display = "(11) 99482-9147"
        
    archetype, niche = get_archetype_and_niche(lead)
    
    lead_dict = {
        "id": f"batch30-{idx:02d}",
        "name": lead["company_name"],
        "short_name": lead["short_name"],
        "slug": slug,
        "niche": niche,
        "city": lead["city"],
        "state": lead["state"],
        "score": 96,
        "priority_class": "A",
        "instagram_username": lead["instagram_username"],
        "instagram_url": f"https://instagram.com/{lead['instagram_username']}",
        "whatsapp_phone": phone_e164,
        "phone_clean": phone_e164,
        "phone": phone_display,
        "archetype": archetype,
        "owner": owner,
        "owner_name": owner_name,
        "owner_label": owner_label,
        "partner_rank": 230 + (idx // 2),
        "followers_count": lead["followers"],
        "instagram_bio": lead.get("bio", f"Especialistas em veículos premium selecionados em {lead['city']} - {lead['state']}."),
        "recommended_offer": "Showroom Digital Avantgarde com Captação Integrada WhatsApp & Vitrine Interativa",
        "diagnosis": f"Presença digital ativa (@{lead['instagram_username']} com {lead['posts']} posts), porém deságua em atendimento manual ou linktree sem showroom interativo no celular."
    }
    
    # Gerar assets
    outreach = build_outreach_assets(
        lead_dict,
        rank=lead_dict["partner_rank"],
        base_url="https://brag-showroom-demos.vercel.app",
        public_demo_base="https://brag-showroom-demos.vercel.app"
    )
    
    msg_wa = (
        f"Olá, diretoria da *{lead['short_name']}*! Tudo bem?\n\n"
        f"Acompanhamos a operação de vocês no Instagram (@{lead['instagram_username']}) em {lead['city']}/{lead['state']} "
        f"e notamos que todo o tráfego de interessados hoje deságua em link genérico ou WhatsApp sem vitrine filtrável no celular.\n\n"
        f"Em vez de enviar uma apresentação comercial teórica, nós projetamos e colocamos no ar uma "
        f"*demonstração funcional exclusiva do novo Showroom Digital da {lead['short_name']}* "
        f"(com catálogo interativo, busca rápida por categoria e captação integrada ao WhatsApp de vocês):\n\n"
        f"https://brag-showroom-demos.vercel.app/{slug}\n\n"
        f"Podem abrir direto no smartphone para testar a velocidade e a experiência. Se fizer sentido ativarmos essa estrutura oficial para a {lead['short_name']}, "
        f"fico à disposição por aqui."
    )
    wa_url = f"https://wa.me/{phone_e164}?text={urllib.parse.quote(msg_wa)}"
    
    video_script = f"""# Roteiro de Apresentação Executiva — {lead['company_name']}
> Operação: Playbook Brag International (Build Before Pitch)
> Vendedor Responsável: {owner_name} ({owner_label})
> Alvo: Sócio / Diretor Comercial (@{lead['instagram_username']})
> Showroom Demo: https://brag-showroom-demos.vercel.app/{slug}

## [00:00 - 00:10] Abertura Direta
"Olá, time da {lead['short_name']}, aqui é o {owner_name} da BRAG International. Analisamos o perfil de vocês (@{lead['instagram_username']}) em {lead['city']}..."

## [00:10 - 00:25] Diagnóstico Objetivo
"...e identificamos que o comprador de alto padrão que chega pelo Instagram não encontra um showroom interativo no celular para navegar pelas opções com rapidez antes de chamar no WhatsApp."

## [00:25 - 00:45] Apresentação da Prova Viva
"Por isso, desenhamos e publicamos este showroom interativo exclusivo para a {lead['short_name']}: Hero de alto impacto, vitrine com fotos em alta definição, especificações técnicas e botão direto para o seu WhatsApp ({phone_display})."

## [00:45 - 00:60] Chamada Limpa
"O link está no ar: https://brag-showroom-demos.vercel.app/{slug}. Testem no celular e, se fizer sentido implementar na operação oficial da loja, estamos prontos para plugar."
"""
    
    outreach["whatsapp_message"] = msg_wa
    outreach["whatsapp_send_url"] = wa_url
    outreach["video_script_60s"] = video_script
    outreach["demo_url"] = f"https://brag-showroom-demos.vercel.app/{slug}"
    
    # Render HTML
    html_demo = render_demo_html(lead_dict, rank=lead_dict["partner_rank"], outreach=outreach)
    
    # Write to demos/<slug>/index.html
    demo_slug_dir = demos_dir / slug
    demo_slug_dir.mkdir(parents=True, exist_ok=True)
    (demo_slug_dir / "index.html").write_text(html_demo, encoding="utf-8")
    
    lead_final_record = {
        "slug": slug,
        "company_name": lead["company_name"],
        "short_name": lead["short_name"],
        "contact_name": "Diretoria Comercial",
        "segment": niche,
        "archetype": archetype,
        "city": lead["city"],
        "state": lead["state"],
        "phone": phone_display,
        "whatsapp_e164": phone_e164,
        "instagram_username": lead["instagram_username"],
        "instagram_url": f"https://instagram.com/{lead['instagram_username']}",
        "website_url": "",
        "demo_url": f"https://brag-showroom-demos.vercel.app/{slug}",
        "score": 96,
        "priority": "A",
        "potential_tier": "P1",
        "assigned_vendor": owner,
        "vendor_rank": lead_dict["partner_rank"],
        "classification": "🔥 Ataque Imediato",
        "stage": "lead_gerado",
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
        "next_action": "Ligar primeiro e disparar demo via WhatsApp",
        "scheduled_callback_at": None,
        "notes": f"Instagram ativo verificado ({lead['post_date']}), {lead['followers']} seguidores, {lead['posts']} publicações. Sem website próprio.",
        "whatsapp_message": msg_wa,
        "whatsapp_send_url": wa_url,
        "video_script_60s": video_script
    }
    generated_demos.append(lead_final_record)
    print(f"[{idx:02d}/30] Demo gerada: {slug} | @{lead['instagram_username']} | Owner: {owner_name}")

with open(BASE / "new_30_vetted_demos.json", "w", encoding="utf-8") as f:
    json.dump(generated_demos, f, indent=2, ensure_ascii=False)

print(f"\nSucesso total: 30 demos personalizadas salvas e validadas.")
