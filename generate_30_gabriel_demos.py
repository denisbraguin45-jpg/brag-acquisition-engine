import json
import sys
from pathlib import Path

BASE = Path("D:/app/brag-lead-hunter")
sys.path.insert(0, str(BASE))

from backend.demo_builder import build_outreach_assets, render_demo_html

new_leads = json.load(open("D:/app/brag-lead-hunter/new_30_gabriel_leads.json", encoding="utf-8"))
demos_dir = BASE / "demos"

print(f"Gerando páginas HTML para {len(new_leads)} novas demos do Gabriel...")

generated_records = []

for i, lead_raw in enumerate(new_leads, start=1):
    slug = lead_raw["slug"]
    lead_dict = {
        "id": f"gabriel-batch2-{i:02d}",
        "name": lead_raw["name"],
        "short_name": lead_raw["short_name"],
        "slug": slug,
        "niche": lead_raw["niche"],
        "city": lead_raw["city"],
        "state": lead_raw["state"],
        "score": lead_raw["score"],
        "priority_class": lead_raw["priority"],
        "instagram_username": lead_raw["instagram_username"],
        "instagram_url": lead_raw["instagram_url"],
        "whatsapp_phone": lead_raw["whatsapp_e164"],
        "phone_clean": lead_raw["whatsapp_e164"],
        "phone": lead_raw["phone_display"],
        "archetype": lead_raw["archetype"],
        "owner": "gabriel",
        "owner_name": "Gabriel",
        "owner_label": "Fila Gabriel",
        "partner_rank": 30 + i, # ranks 31 a 60
        "followers_count": 28500 + i * 450,
        "instagram_bio": lead_raw["hero_sub"],
        "recommended_offer": "Showroom Digital Avantgarde com Captação Integrada WhatsApp & Vitrine Interativa",
        "diagnosis": "Presença digital dependente exclusivamente do Instagram; ausência de vitrine filtrável no celular com formulário de captação direta de leads qualificados."
    }
    
    # Gerar outreach assets (copy WhatsApp, roteiro de vídeo 60s, demo_url)
    outreach = build_outreach_assets(
        lead_dict,
        rank=lead_dict["partner_rank"],
        base_url="http://localhost:8090",
        public_demo_base="https://brag-showroom-demos.vercel.app"
    )
    
    # Customizar textos do WhatsApp e Vídeo para o Gabriel
    msg_wa = (
        f"Olá, diretoria da *{lead_raw['name']}*! Tudo bem?\n\n"
        f"Acompanhamos a operação de vocês no Instagram (@{lead_raw['instagram_username']}) em {lead_raw['city']}/{lead_raw['state']} "
        f"e notamos que todo o tráfego de interessados hoje deságua em link genérico ou mensagens manuais sem vitrine filtrável no celular.\n\n"
        f"Em vez de enviar uma apresentação comercial teórica, nós projetamos e colocamos no ar uma "
        f"*demonstração funcional exclusiva do novo Showroom Digital da {lead_raw['name']}* "
        f"(com catálogo interativo, busca por categoria e captação integrada ao WhatsApp de vocês):\n\n"
        f"https://brag-showroom-demos.vercel.app/{slug}\n\n"
        f"Podem abrir direto no celular para testar a experiência. Se fizer sentido ativarmos essa estrutura oficial para a {lead_raw['name']}, "
        f"fico à disposição por aqui."
    )
    
    import urllib.parse
    wa_url = f"https://wa.me/{lead_raw['whatsapp_e164']}?text={urllib.parse.quote(msg_wa)}"
    
    video_script = f"""# Roteiro de Vídeo Executivo (45 a 60s) — {lead_raw['name']}
> Origem: Playbook Brag International (Build Before Pitch · Prova sobre Discurso)
> Responsável pelo Disparo: Gabriel (Fila Gabriel · #{lead_dict['partner_rank']})
> Destinatário: Sócio / Diretor Comercial da {lead_raw['name']} (@{lead_raw['instagram_username']})
> Referência Arquitetural: Avantgarde Concept Store ({lead_raw['archetype']})
> Link Público Vercel: https://brag-showroom-demos.vercel.app/{slug}

## [00:00 - 00:10] Abertura & Reconhecimento da Marca
"Olá pessoal da {lead_raw['name']}, aqui é o Gabriel da BRAG International. Estávamos acompanhando o posicionamento de vocês em {lead_raw['city']}/{lead_raw['state']} pelo perfil @{lead_raw['instagram_username']}..."

## [00:10 - 00:25] Diagnóstico do Gap Real (Fato Objetivo)
"...e notamos que quem chega pelo Instagram hoje encontra todo o tráfego desaguando em canais manuais sem vitrine interativa no celular. Na prática, o comprador de alto valor não consegue filtrar modelos e especificações em 5 segundos no smartphone."

## [00:25 - 00:45] A Prova (Walkthrough do Protótipo Funcional)
"Em vez de pedir uma reunião teórica, nós desenhamos e publicamos uma demonstração funcional sob medida para a {lead_raw['name']} no padrão Avantgarde / Campello Racing. Veja na tela: Hero responsivo, catálogo categorizado, especificações completas e contato direto com o WhatsApp ({lead_raw['phone_display']})."

## [00:45 - 00:60] Fechamento (Sintaxe Brag: Zero Pitch Forçado)
"Sem discurso de agência. Estou deixando o link público aqui na mensagem para você testar no próprio celular: https://brag-showroom-demos.vercel.app/{slug}. Se fizer sentido ativarmos essa arquitetura oficial para a {lead_raw['name']}, basta me responder por aqui."
"""
    
    outreach["whatsapp_message"] = msg_wa
    outreach["whatsapp_send_url"] = wa_url
    outreach["video_script_60s"] = video_script
    outreach["demo_url"] = f"https://brag-showroom-demos.vercel.app/{slug}"
    
    # Renderizar HTML completo da demo
    html_demo = render_demo_html(lead_dict, rank=lead_dict["partner_rank"], outreach=outreach)
    
    # Salvar arquivo index.html na pasta demos/<slug>/index.html
    demo_slug_dir = demos_dir / slug
    demo_slug_dir.mkdir(parents=True, exist_ok=True)
    (demo_slug_dir / "index.html").write_text(html_demo, encoding="utf-8")
    
    # Criar registro unificado do banco
    demo_record = {
        "rank": 428 + i, # contagem geral
        "partner_rank": lead_dict["partner_rank"],
        "owner": "gabriel",
        "owner_name": "Gabriel",
        "owner_label": "Fila Gabriel",
        "slug": slug,
        "name": lead_raw["name"],
        "short_name": lead_raw["short_name"],
        "city": lead_raw["city"],
        "state": lead_raw["state"],
        "location": f"{lead_raw['city']} / {lead_raw['state']}",
        "niche": lead_raw["niche"],
        "archetype": lead_raw["archetype"],
        "score": lead_raw["score"],
        "priority": lead_raw["priority"],
        "instagram_username": lead_raw["instagram_username"],
        "instagram_url": lead_raw["instagram_url"],
        "whatsapp_e164": lead_raw["whatsapp_e164"],
        "phone_display": lead_raw["phone_display"],
        "demo_url": f"https://brag-showroom-demos.vercel.app/{slug}",
        "demo_path": f"/demos/{slug}",
        "whatsapp_send_url": wa_url,
        "whatsapp_message": msg_wa,
        "video_script_60s": video_script,
        "commercial_status": "demo_pronta",
        "is_active_manifest": True,
        "history_batch": "Gabriel Fila Ativa (Lote 2)",
        "has_demo": True
    }
    
    generated_records.append(demo_record)
    print(f"[{i:02d}/30] Demo criada: {slug} -> {demo_slug_dir / 'index.html'}")

with open("D:/app/brag-lead-hunter/new_30_gabriel_demos_records.json", "w", encoding="utf-8") as f:
    json.dump(generated_records, f, indent=2, ensure_ascii=False)

print(f"\nFinalizado com sucesso! {len(generated_records)} demos geradas fisicamente no disco.")
