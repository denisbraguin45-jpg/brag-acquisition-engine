import json
import sqlite3
import datetime
from typing import Optional, Any
from backend.sales_db import DB_PATH

SCRIPTS = {

    "script_1": {
        "id": "script_1",
        "title": "SCRIPT 1 — PRIMEIRA LIGAÇÃO",
        "stage": "primeira_ligacao",
        "text": """Olá, tudo bem? Aqui é {vendedor}, da BRAG International.

Estou entrando em contato porque analisamos a presença digital da {empresa} e preparamos uma demonstração personalizada de como ela poderia apresentar seus produtos e serviços de forma mais profissional na internet.

Gostaria de falar rapidamente com o responsável pela empresa. Ele está disponível?"""
    },
    "script_2": {
        "id": "script_2",
        "title": "SCRIPT 2 — FALAR COM O DECISOR",
        "stage": "decisor",
        "text": """Perfeito. Nós desenvolvemos uma demonstração para a {empresa}, pensando em como apresentar melhor os produtos, fortalecer a presença digital e facilitar o contato de potenciais clientes.

Gostaria de te mostrar o projeto. Você consegue dedicar dois minutos?"""
    },
    "script_3": {
        "id": "script_3",
        "title": "SCRIPT 3 — APRESENTAÇÃO DA DEMO",
        "stage": "apresentacao_demo",
        "text": """Essa demonstração foi desenvolvida considerando a identidade da sua empresa.

A proposta é transformar o site em uma verdadeira vitrine comercial, onde seus clientes conseguem visualizar os produtos, conhecer a empresa e entrar em contato com mais facilidade.

O projeto já está estruturado ({demo_url}). Podemos conversar sobre a implementação?"""
    },
    "script_4": {
        "id": "script_4",
        "title": "SCRIPT 4 — CLIENTE INTERESSADO",
        "stage": "qualificacao",
        "text": """Perfeito. O próximo passo é alinharmos a implementação e os detalhes do projeto.

Nossa equipe já preparou a estrutura inicial, então conseguimos avançar diretamente para a entrega."""
    },
    "script_5": {
        "id": "script_5",
        "title": "SCRIPT 5 — OBJEÇÃO: JÁ TENHO INSTAGRAM",
        "stage": "objecao_instagram",
        "text": """Excelente. O Instagram é importante, mas o site cumpre outro papel: funciona como uma estrutura própria para apresentar sua empresa e seus produtos, organizar informações e facilitar o contato comercial.

A ideia não é substituir o Instagram, mas complementar sua presença digital."""
    },
    "script_6": {
        "id": "script_6",
        "title": "SCRIPT 6 — OBJEÇÃO: ESTÁ CARO",
        "stage": "objecao_caro",
        "text": """Entendo perfeitamente. A questão é avaliar o valor que uma presença digital profissional pode agregar à empresa.

Não estamos oferecendo apenas uma página, mas uma estrutura comercial para apresentar melhor seus produtos e facilitar oportunidades de negócio."""
    },
    "script_7": {
        "id": "script_7",
        "title": "SCRIPT 7 — OBJEÇÃO: VOU PENSAR",
        "stage": "objecao_pensar",
        "text": """Claro. Só gostaria de entender uma coisa: existe alguma dúvida específica sobre o projeto, o investimento ou a implementação que eu possa esclarecer agora?"""
    },
    "script_8": {
        "id": "script_8",
        "title": "SCRIPT 8 — NÃO ATENDEU (REAGENDAR)",
        "stage": "nao_atendeu",
        "text": """(Sem contato direto) Registrar tentativa de chamada sem resposta e programar nova ligação para outro turno/horário. Oportunidade mantida ativa no pipeline."""
    },
    "script_9": {
        "id": "script_9",
        "title": "SCRIPT 9 — FOLLOW-UP",
        "stage": "follow_up",
        "text": """Olá, {nome}. Tudo bem?

Conseguiu avaliar a demonstração que preparamos para a {empresa}?

Gostaria de saber sua opinião e entender se podemos avançar com a implementação."""
    },
    "script_mensagem": {
        "id": "script_mensagem",
        "title": "SCRIPT DE MENSAGEM — WHATSAPP & INSTAGRAM DIRECT",
        "stage": "mensagem_direta",
        "text": """Olá, diretoria da *{empresa}*! Tudo bem? Aqui é {vendedor}, da BRAG International.

Acompanhamos a presença de vocês no Instagram e notamos que a vitrine digital de vocês ainda não conta com um catálogo moderno, rápido e com showroom filtrável no celular.

Em vez de enviar uma apresentação comercial teórica, nós desenvolvemos e colocamos no ar uma demonstração personalizada exclusiva para a *{empresa}*:

{demo_url}

Podem abrir direto no celular para testar a experiência. O projeto já está estruturado. Gostaria de entender se faz sentido ativarmos essa vitrine oficial para vocês!"""
    }
}

SCRIPTS_MAP = SCRIPTS

def get_sales_leads(vendor: Optional[str] = None, classification: Optional[str] = None, priority: Optional[str] = None) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT * FROM SALES_LEADS WHERE 1=1"
    params = []
    if vendor and vendor != "all":
        query += " AND assigned_vendor = ?"
        params.append(vendor)
    if classification and classification != "all":
        query += " AND classification = ?"
        params.append(classification)
    if priority and priority != "all":
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY assigned_vendor, vendor_rank"
    c.execute(query, params)
    cols = [col[0] for col in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows

def get_sales_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    stats = {}
    for v in ["bruce", "gabriel", "general"]:
        where_clause = "" if v == "general" else f"WHERE assigned_vendor = '{v}'"
        c.execute(f"""
        SELECT
            count(*),
            sum(calls_made),
            sum(calls_answered),
            sum(decision_maker_contacted),
            sum(demo_presented),
            sum(interested),
            sum(proposal_sent),
            sum(negotiation_opened),
            sum(deal_closed),
            sum(deal_value),
            count(CASE WHEN scheduled_callback_at IS NOT NULL AND scheduled_callback_at != '' THEN 1 END),
            count(CASE WHEN classification = 'HOT' THEN 1 END),
            count(CASE WHEN classification = 'WARM' THEN 1 END),
            count(CASE WHEN classification = 'COLD' THEN 1 END),
            count(CASE WHEN classification = 'LOST' THEN 1 END)
        FROM SALES_LEADS
        {where_clause}
        """)
        row = c.fetchone()
        total_leads = row[0] or 0
        calls_made = row[1] or 0
        calls_answered = row[2] or 0
        decisors = row[3] or 0
        demos = row[4] or 0
        interested = row[5] or 0
        proposals = row[6] or 0
        negotiations = row[7] or 0
        deals = row[8] or 0
        revenue = row[9] or 0.0
        callbacks = row[10] or 0
        hot = row[11] or 0
        warm = row[12] or 0
        cold = row[13] or 0
        lost = row[14] or 0

        conv_rate = (deals / total_leads * 100.0) if total_leads > 0 else 0.0
        stats[v] = {
            "total_leads": total_leads,
            "calls_made": calls_made,
            "calls_answered": calls_answered,
            "decision_maker_contacted": decisors,
            "demo_presented": demos,
            "interested": interested,
            "proposal_sent": proposals,
            "negotiation_opened": negotiations,
            "deal_closed": deals,
            "revenue": revenue,
            "conversion_rate": round(conv_rate, 2),
            "scheduled_callbacks": callbacks,
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "lost": lost
        }

    conn.close()
    return stats

def record_interaction(
    slug: str,
    vendor: str,
    interaction_type: str,
    script_used: Optional[str] = None,
    call_outcome: Optional[str] = None,
    notes: Optional[str] = None,
    next_action: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    new_classification: Optional[str] = None,
    new_stage: Optional[str] = None,
    deal_value: Optional[float] = None
) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now_iso = datetime.datetime.now().isoformat()

    # Get current lead
    c.execute("SELECT * FROM SALES_LEADS WHERE slug = ?", (slug,))
    col_names = [col[0] for col in c.description]
    lead_row = c.fetchone()
    if not lead_row:
        conn.close()
        raise ValueError(f"Lead with slug '{slug}' not found.")
    lead = dict(zip(col_names, lead_row))

    # Calculate increment counters based on outcome / interaction
    calls_made = lead["calls_made"]
    calls_answered = lead["calls_answered"]
    decisors = lead["decision_maker_contacted"]
    demos = lead["demo_presented"]
    interested = lead["interested"]
    proposals = lead["proposal_sent"]
    negotiations = lead["negotiation_opened"]
    closed = lead["deal_closed"]
    val = lead["deal_value"]

    if interaction_type == "call":
        calls_made += 1
        if call_outcome in ["answered", "decision_maker", "interested", "meeting_set", "objection"]:
            calls_answered += 1
        if call_outcome == "decision_maker" or new_stage in ["decisor", "apresentacao_demo", "qualificacao", "proposta", "negociacao", "fechamento"]:
            decisors = max(decisors, 1)

    if new_stage == "apresentacao_demo" or interaction_type == "demo_viewed":
        demos = max(demos, 1)
    if new_stage in ["qualificacao", "proposta", "negociacao"] or call_outcome == "interested" or new_classification == "HOT":
        interested = max(interested, 1)
    if new_stage == "proposta" or interaction_type == "proposal":
        proposals = max(proposals, 1)
    if new_stage == "negociacao":
        negotiations = max(negotiations, 1)
    if new_stage == "fechamento" or interaction_type == "deal_closed":
        closed = 1
        if deal_value is not None:
            val = float(deal_value)

    # Classification logic
    final_classification = new_classification or lead["classification"]
    final_stage = new_stage or lead["stage"]

    # Rule 5: HOT = Empresa interessada, decisor identificado ou negociação iniciada
    if final_stage in ["qualificacao", "proposta", "negociacao"]:
        final_classification = "HOT"
    elif final_stage == "fechamento":
        final_classification = "HOT"
    elif final_stage == "perdido":
        final_classification = "LOST"

    # Rule 6: Todo lead HOT deve ter uma próxima ação definida
    final_next_action = next_action or lead["next_action"]
    if final_classification == "HOT" and not final_next_action:
        final_next_action = "Apresentar proposta / Fechamento de contrato no mesmo dia"

    final_callback = scheduled_at if scheduled_at is not None else lead["scheduled_callback_at"]
    final_notes = ((lead["notes"] + " | " + notes) if (lead["notes"] and notes) else (notes or lead["notes"]))

    # Update SALES_LEADS
    c.execute("""
    UPDATE SALES_LEADS SET
        calls_made = ?,
        calls_answered = ?,
        decision_maker_contacted = ?,
        demo_presented = ?,
        interested = ?,
        proposal_sent = ?,
        negotiation_opened = ?,
        deal_closed = ?,
        deal_value = ?,
        classification = ?,
        stage = ?,
        last_interaction_at = ?,
        next_action = ?,
        scheduled_callback_at = ?,
        notes = ?,
        updated_at = ?
    WHERE slug = ?
    """, (
        calls_made, calls_answered, decisors, demos, interested, proposals,
        negotiations, closed, val, final_classification, final_stage,
        now_iso, final_next_action, final_callback, final_notes, now_iso, slug
    ))

    # Insert into SALES_INTERACTIONS
    c.execute("""
    INSERT INTO SALES_INTERACTIONS (
        slug, vendor, interaction_type, script_used, call_outcome, notes,
        next_action, scheduled_at, deal_value, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        slug, vendor, interaction_type, script_used, call_outcome, notes,
        final_next_action, final_callback, val, now_iso
    ))

    conn.commit()

    # Re-fetch updated lead
    c.execute("SELECT * FROM SALES_LEADS WHERE slug = ?", (slug,))
    updated_lead = dict(zip(col_names, c.fetchone()))
    conn.close()

    return updated_lead

def get_lead_interactions(slug: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM SALES_INTERACTIONS WHERE slug = ? ORDER BY id DESC", (slug,))
    cols = [col[0] for col in c.description]
    rows = [dict(zip(cols, r)) for r in c.fetchall()]
    conn.close()
    return rows


def delete_sales_lead(slug: str) -> dict[str, Any]:
    """Exclui um lead invalido do banco de dados SQLite e dos arquivos de distribuicao."""
    import os
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT company_name FROM SALES_LEADS WHERE slug = ?", (slug,))
    row = c.fetchone()
    name = row[0] if row else slug

    c.execute("DELETE FROM SALES_LEADS WHERE slug = ?", (slug,))
    c.execute("DELETE FROM SALES_INTERACTIONS WHERE slug = ?", (slug,))
    c.execute("DELETE FROM COMPANIES WHERE company_slug = ? OR id = ?", (slug, slug))
    conn.commit()
    conn.close()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_path = os.path.join(base_dir, 'demos', 'sales_distribution_400.json')
    if os.path.exists(dist_path):
        try:
            with open(dist_path, 'r', encoding='utf-8') as f_dist:
                dist_data = json.load(f_dist)
            if isinstance(dist_data, list):
                dist_data = [x for x in dist_data if x.get('slug') != slug]
                with open(dist_path, 'w', encoding='utf-8') as f_dist:
                    json.dump(dist_data, f_dist, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao remover de sales_distribution_400: {e}")

    crm_path = os.path.join(base_dir, 'demos', 'crm_all_leads.json')
    if os.path.exists(crm_path):
        try:
            with open(crm_path, 'r', encoding='utf-8') as f_crm:
                crm_data = json.load(f_crm)
            if isinstance(crm_data, list):
                crm_data = [x for x in crm_data if x.get('slug') != slug]
                with open(crm_path, 'w', encoding='utf-8') as f_crm:
                    json.dump(crm_data, f_crm, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao remover de crm_all_leads: {e}")

    return {"ok": True, "slug": slug, "company_name": name, "message": f"Lead {name} excluido com sucesso"}
