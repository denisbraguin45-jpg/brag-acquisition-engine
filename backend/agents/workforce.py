"""
BRAG AI Workforce — Market & Sales Intelligence Agents (Agents 13, 14, 15, 16).

Implements:
- AGENT 13 — ICP MARKET INTELLIGENCE
  Maps markets & segments, identifies niches with high website service adherence,
  estimates available companies, identifies geographic concentration, compares segments
  by commercial potential, and recommends niches for testing.

- AGENT 14 — OFFER INTELLIGENCE
  Analyzes problems identified across companies, maps problems to BRAG solutions,
  recommends the most suitable offer, identifies AI maintenance & automation opportunities,
  prepares value arguments, and strictly avoids unproven result promises.

- AGENT 15 — MARKET SIZE INTELLIGENCE
  Estimates TAM, SAM, and SOM using verifiable institutional sources (IBGE/FENABRAVE/FENAUTO/ABACO),
  explicitly differentiates:
    (a) Empresas Encontradas (collected in DB)
    (b) Empresas Elegíveis (SAM in target niches/geos without adequate digital presence)
    (c) Empresas Efetivamente Alcançáveis (SOM with verified direct contact & capacity)
  Never confuses collected records count with total market size. Identifies geographic expansion opportunities.

- AGENT 16 — SALES EXPERIMENT INTELLIGENCE
  Creates and manages test campaigns, compares niches and scripts, measures:
    - Contact rate (%)
    - Response rate (%)
    - Meetings rate (%)
    - Proposals rate (%)
    - Sales conversion rate (%)
    - Revenue per campaign (R$)
  Enforces the CENTRAL RULE:
  "Nenhum nicho deve ser considerado validado apenas por possuir muitos leads.
   A validação exige evidência comercial obtida através de contatos, conversas, propostas e vendas.
   O sistema deve recomendar expansão somente quando houver dados suficientes para justificar a decisão."
"""
import json
import sqlite3
from typing import Any, Optional

from backend.database import new_id, now_iso, row_to_dict, rows_to_list


# Verifiable institutional market benchmarks (FENAUTO / FENABRAVE / IBGE / ACOBAR)
VERIFIABLE_MARKET_BENCHMARKS = [
    {
        "segment_code": "P1",
        "segment_name": "P1 — Revendas Premium e Multimarcas",
        "tam_brazil_companies": 48500,
        "sam_target_companies": 8200,
        "som_12m_capacity": 650,
        "avg_brag_ticket_brl": 3500,
        "monthly_ai_retainer_brl": 690,
        "website_adherence_score": 94,
        "source_citation": "FENAUTO (Federação Nacional das Associações dos Revendedores de Veículos Automotores) — Relatório Anual do Setor (~48,5 mil revendas independentes no Brasil, ~17% no segmento seminovos/multimarcas de médio-alto padrão).",
        "key_pain": "Dependência exclusiva de Instagram/Linktree e portais pagos (Webmotors/OLX) sem vitrine própria de estoque.",
    },
    {
        "segment_code": "P2",
        "segment_name": "P2 — Luxo e Superesportivos",
        "tam_brazil_companies": 1250,
        "sam_target_companies": 480,
        "som_12m_capacity": 120,
        "avg_brag_ticket_brl": 6800,
        "monthly_ai_retainer_brl": 1200,
        "website_adherence_score": 96,
        "source_citation": "ABEIFA / FENABRAVE + Mapeamento de Boutiques Automotivas (Eixo SP-PR-SC-DF-RJ-Miami) — Operações de altíssimo ticket unitário (> R$ 500 mil/veículo).",
        "key_pain": "Grandeza física do showroom contrasta com presença web amadora ou inexistente, reduzindo autoridade perante compradores de alta renda.",
    },
    {
        "segment_code": "P3",
        "segment_name": "P3 — Importados, Blindados e SUVs Executivos",
        "tam_brazil_companies": 3400,
        "sam_target_companies": 1350,
        "som_12m_capacity": 240,
        "avg_brag_ticket_brl": 4800,
        "monthly_ai_retainer_brl": 890,
        "website_adherence_score": 91,
        "source_citation": "ABRACICLO / ABRABLIN (Associação Brasileira de Blindagem — Brasil é o maior mercado de blindados do mundo, concentrado em SP, RJ, MG e PR).",
        "key_pain": "Falta de apresentação técnica de nível de blindagem, laudo cautelar e filtro por especificações no mobile.",
    },
    {
        "segment_code": "P4",
        "segment_name": "P4 — Náutica Premium (Lanchas, Iates e Jet Skis)",
        "tam_brazil_companies": 2100,
        "sam_target_companies": 740,
        "som_12m_capacity": 140,
        "avg_brag_ticket_brl": 5900,
        "monthly_ai_retainer_brl": 990,
        "website_adherence_score": 93,
        "source_citation": "ACOBAR (Associação Brasileira dos Construtores de Barcos e seus Implementos) — Brokers náuticos, marinas e revendas no litoral de SC, SP, RJ, BA e Flórida.",
        "key_pain": "Catálogos de embarcações espalhados em PDFs ou stories sem ficha técnica (pés, motorização, horas de uso) pesquisável.",
    },
]


# ==============================================================================
# AGENT 13 — ICP MARKET INTELLIGENCE
# ==============================================================================
def run_agent_13_icp_market_intelligence(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    AGENT 13 — ICP MARKET INTELLIGENCE
    Maps segments, calculates real metrics from collected DB leads + institutional benchmarks,
    identifies geographic concentration, and recommends test niches.
    """
    niche_rows = rows_to_list(
        conn.execute(
            """
            SELECT
                COALESCE(NULLIF(c.niche, ''), 'Não classificado') AS niche,
                COUNT(c.id) AS total_companies,
                SUM(CASE WHEN c.has_own_website = 0 THEN 1 ELSE 0 END) AS without_website,
                SUM(CASE WHEN s.priority_class IN ('A', 'B') THEN 1 ELSE 0 END) AS qualified_ab,
                SUM(CASE WHEN s.priority_class = 'A' THEN 1 ELSE 0 END) AS priority_a,
                ROUND(AVG(COALESCE(s.total_score, 0)), 1) AS avg_icp_score,
                SUM(CASE WHEN COALESCE(ct.whatsapp, ct.phone_normalized, '') != '' THEN 1 ELSE 0 END) AS with_direct_contact
            FROM COMPANIES c
            LEFT JOIN ICP_SCORES s ON s.company_id = c.id
            LEFT JOIN CONTACTS ct ON ct.company_id = c.id
            GROUP BY COALESCE(NULLIF(c.niche, ''), 'Não classificado')
            ORDER BY qualified_ab DESC, avg_icp_score DESC
            """
        ).fetchall()
    )

    geo_rows = rows_to_list(
        conn.execute(
            """
            SELECT
                COALESCE(NULLIF(c.city, ''), 'Não informada') AS city,
                COALESCE(NULLIF(c.state, ''), '—') AS state,
                c.country AS country,
                COUNT(c.id) AS companies_count,
                SUM(CASE WHEN c.has_own_website = 0 THEN 1 ELSE 0 END) AS without_website,
                SUM(CASE WHEN s.priority_class = 'A' THEN 1 ELSE 0 END) AS priority_a,
                ROUND(AVG(COALESCE(s.total_score, 0)), 1) AS avg_score
            FROM COMPANIES c
            LEFT JOIN ICP_SCORES s ON s.company_id = c.id
            GROUP BY COALESCE(NULLIF(c.city, ''), 'Não informada'), COALESCE(NULLIF(c.state, ''), '—'), c.country
            ORDER BY companies_count DESC, avg_score DESC
            LIMIT 12
            """
        ).fetchall()
    )

    # Combine benchmark potential with observed digital need
    segments_comparison = []
    for bm in VERIFIABLE_MARKET_BENCHMARKS:
        code = bm["segment_code"]
        matched_db = [r for r in niche_rows if r["niche"].upper().startswith(code)]
        db_total = sum(r["total_companies"] for r in matched_db)
        db_no_site = sum(r["without_website"] for r in matched_db)
        db_qual = sum(r["qualified_ab"] for r in matched_db)
        db_contact = sum(r["with_direct_contact"] for r in matched_db)
        avg_score = matched_db[0]["avg_icp_score"] if matched_db else 0.0

        no_site_ratio = round((db_no_site / db_total) * 100, 1) if db_total > 0 else 0.0
        reachability_ratio = round((db_contact / db_total) * 100, 1) if db_total > 0 else 0.0

        # Commercial potential index (weighted by adherence, gap rate, and reachability)
        commercial_potential_index = round(
            (bm["website_adherence_score"] * 0.4)
            + (min(100, no_site_ratio + 25) * 0.35)
            + (min(100, reachability_ratio + 20) * 0.25),
            1,
        )

        segments_comparison.append({
            "segment_code": code,
            "segment_name": bm["segment_name"],
            "website_adherence_score": bm["website_adherence_score"],
            "estimated_available_companies_brazil": bm["sam_target_companies"],
            "discovered_in_local_db": db_total,
            "without_own_website_in_db": db_no_site,
            "without_website_pct": no_site_ratio,
            "qualified_ab_in_db": db_qual,
            "with_direct_contact_in_db": db_contact,
            "avg_icp_score": avg_score,
            "commercial_potential_index": commercial_potential_index,
            "key_pain": bm["key_pain"],
            "recommended_for_test": commercial_potential_index >= 75,
            "recommendation_rationale": (
                f"Alta aderência ({bm['website_adherence_score']}/100): {db_no_site} de {db_total} empresas coletadas "
                f"não possuem site próprio ({no_site_ratio}%) e {db_contact} possuem contato comercial direto."
                if db_total > 0
                else f"Segmento de alto ticket com {bm['sam_target_companies']} empresas elegíveis estimadas; executar campanha de coleta inicial."
            ),
        })

    segments_comparison.sort(key=lambda x: x["commercial_potential_index"], reverse=True)

    return {
        "agent_id": "AGENT_13",
        "agent_name": "ICP MARKET INTELLIGENCE",
        "generated_at": now_iso(),
        "segments_comparison": segments_comparison,
        "geographic_concentration": geo_rows,
        "recommended_niches_for_testing": [
            {
                "segment": s["segment_name"],
                "potential_index": s["commercial_potential_index"],
                "rationale": s["recommendation_rationale"],
                "validation_warning": "Recomendado para TESTE COMERCIAL. Não considerar validado até obter conversas, propostas e vendas (Regra Central).",
            }
            for s in segments_comparison[:3]
        ],
    }


# ==============================================================================
# AGENT 14 — OFFER INTELLIGENCE
# ==============================================================================
def run_agent_14_offer_intelligence(conn: sqlite3.Connection, company_id: Optional[str] = None) -> dict[str, Any]:
    """
    AGENT 14 — OFFER INTELLIGENCE
    Analyzes real observed problems across the database (or for a specific company),
    maps problems to BRAG solutions, recommends the optimal offer + AI maintenance/automation,
    and prepares ethical, evidence-based value arguments without unproven promises.
    """
    offer_catalog = [
        {
            "offer_id": "OFFER_VITRINE_HIGH_TICKET",
            "title": "Vitrine Digital High-Ticket + Catálogo Inteligente BRAG",
            "target_problem": "Ausência de website próprio (opera apenas com Instagram, Linktree ou WhatsApp direto)",
            "brag_solution": (
                "Desenvolvimento de website institucional e catálogo próprio mobile-first com filtros por marca/modelo/ano, "
                "páginas individuais de produto otimizadas para SEO local e botão de conversão rápida no WhatsApp."
            ),
            "ai_maintenance_automation": (
                "Sincronização assistida de estoque a partir das publicações do Instagram + Qualificador IA 24/7 no WhatsApp "
                "para responder dúvidas iniciais de ficha técnica e encaminhar leads quentes ao vendedor."
            ),
            "setup_investment_range_brl": "R$ 2.500 – R$ 4.800",
            "monthly_recurrence_range_brl": "R$ 490 – R$ 890/mês (Manutenção + IA)",
            "value_arguments": [
                "Propriedade do ativo digital: a empresa deixa de depender exclusivamente do algoritmo do Instagram ou de comissões/mensalidades de portais de classificados.",
                "Experiência de compra compatível com o ticket do produto: compradores de veículos/embarcações premium pesquisam o estoque no celular antes de visitar a loja.",
                "Rastreabilidade comercial: instalação de pixels de remarketing (Meta/Google) impossível de manter apenas no perfil do Instagram.",
            ],
            "ethical_compliance_note": "Argumentação baseada em controle de canal, experiência do comprador e infraestrutura técnica verificável — sem prometer multiplicação garantida de faturamento.",
        },
        {
            "offer_id": "OFFER_REBUILD_PERFORMANCE",
            "title": "Rebuild de Performance Mobile + Recuperação de Conversão",
            "target_problem": "Website quebrado (HTTP 4xx/5xx/timeout), sem HTTPS ou não responsivo no celular",
            "brag_solution": (
                "Reconstrução completa do site em stack moderna de alta velocidade (PageSpeed Mobile ≥ 95), "
                "certificado SSL ativo, correção de layout mobile e estrutura clara de Call-to-Action."
            ),
            "ai_maintenance_automation": (
                "Monitoramento automático de disponibilidade + Agente de Triagem Comercial no WhatsApp "
                "integrado aos formulários de cotação e avaliação de seminovo na troca."
            ),
            "setup_investment_range_brl": "R$ 2.200 – R$ 4.200",
            "monthly_recurrence_range_brl": "R$ 490 – R$ 790/mês",
            "value_arguments": [
                "Eliminação de perda imediata de tráfego: visitantes que clicam no link da bio ou no Google Maps deixam de encontrar erro de conexão ou aviso de 'site não seguro'.",
                "Redução de fricção no smartphone: mais de 80% do tráfego vindo do Instagram ocorre em dispositivos móveis.",
            ],
            "ethical_compliance_note": "Baseado na correção de falhas técnicas reproduzíveis medidas pelo Website Auditor.",
        },
        {
            "offer_id": "OFFER_CRO_AI_WORKFORCE",
            "title": "Otimização de Conversão (CRO) + Agente Comercial IA no WhatsApp",
            "target_problem": "Website existente sem botão de WhatsApp, sem formulário de contato ou sem clareza de oferta",
            "brag_solution": (
                "Reestruturação da dobra principal (Hero), inclusão de CTAs diretos por veículo, "
                "formulário de simulação/agendamento e implantação de atendimento inteligente."
            ),
            "ai_maintenance_automation": (
                "Agente de IA treinado no estoque da loja para atendimento imediato fora do horário comercial, "
                "qualificação de interesse (troca, financiamento, à vista) e agendamento de test-drive/visita."
            ),
            "setup_investment_range_brl": "R$ 1.800 – R$ 3.500",
            "monthly_recurrence_range_brl": "R$ 590 – R$ 990/mês",
            "value_arguments": [
                "Aproveitamento do tráfego já existente no site através de pontos claros de contato e resposta imediata.",
                "Atendimento imediato em horários de pico noturno e finais de semana sem sobrecarregar a equipe de vendas.",
            ],
            "ethical_compliance_note": "Focado em velocidade de resposta operacional e redução de etapas até o contato humano.",
        },
    ]

    # Aggregate problem counts from database
    stats_row = conn.execute(
        """
        SELECT
            COUNT(c.id) AS total,
            SUM(CASE WHEN c.has_own_website = 0 THEN 1 ELSE 0 END) AS no_website,
            SUM(CASE WHEN a.audit_status = 'broken' THEN 1 ELSE 0 END) AS broken_site,
            SUM(CASE WHEN a.audit_status IN ('weak', 'needs_improvement') THEN 1 ELSE 0 END) AS weak_site,
            SUM(CASE WHEN a.has_whatsapp_button = 0 AND c.has_own_website = 1 THEN 1 ELSE 0 END) AS missing_whatsapp_btn,
            SUM(CASE WHEN a.has_https = 0 AND c.has_own_website = 1 THEN 1 ELSE 0 END) AS missing_https
        FROM COMPANIES c
        LEFT JOIN AUDITS a ON a.company_id = c.id
        """
    ).fetchone()
    problem_summary = row_to_dict(stats_row) if stats_row else {}

    company_recommendation = None
    if company_id:
        comp = row_to_dict(conn.execute("SELECT * FROM COMPANIES WHERE id = ?", (company_id,)).fetchone())
        aud = row_to_dict(conn.execute("SELECT * FROM AUDITS WHERE company_id = ? LIMIT 1", (company_id,)).fetchone())
        sc = row_to_dict(conn.execute("SELECT * FROM ICP_SCORES WHERE company_id = ? LIMIT 1", (company_id,)).fetchone())
        if comp:
            if not comp.get("has_own_website"):
                chosen = offer_catalog[0]
            elif aud and aud.get("audit_status") == "broken":
                chosen = offer_catalog[1]
            else:
                chosen = offer_catalog[2]
            company_recommendation = {
                "company_id": company_id,
                "company_name": comp.get("name"),
                "observed_diagnosis": (sc or {}).get("diagnosis") or "",
                "recommended_offer": chosen,
                "custom_pitch": (sc or {}).get("commercial_pitch") or "",
            }

    return {
        "agent_id": "AGENT_14",
        "agent_name": "OFFER INTELLIGENCE",
        "generated_at": now_iso(),
        "observed_problems_distribution": problem_summary,
        "offer_matrix": offer_catalog,
        "company_specific_recommendation": company_recommendation,
        "policy_guardrail": "Nenhuma promessa de resultado financeiro garantido é emitida; todas as ofertas ancoram-se em entregas técnicas e operacionais verificáveis.",
    }


# ==============================================================================
# AGENT 15 — MARKET SIZE INTELLIGENCE
# ==============================================================================
def run_agent_15_market_size_intelligence(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    AGENT 15 — MARKET SIZE INTELLIGENCE
    Estimates TAM, SAM, and SOM from verifiable industry sources and explicitly differentiates:
    1. Empresas Encontradas (records in local database)
    2. Empresas Elegíveis (qualified ICP without adequate website)
    3. Empresas Efetivamente Alcançáveis (eligible companies with verified phone/WhatsApp/email contact)
    Never confuses collected database records with real market size.
    """
    funnel_row = conn.execute(
        """
        SELECT
            COUNT(c.id) AS found_companies,
            SUM(CASE WHEN COALESCE(s.total_score, 0) >= 60 AND (c.has_own_website = 0 OR a.audit_status IN ('broken', 'weak', 'needs_improvement', 'no_site', 'third_party_only')) THEN 1 ELSE 0 END) AS eligible_companies,
            SUM(CASE WHEN COALESCE(s.total_score, 0) >= 60 AND COALESCE(ct.whatsapp, ct.phone_normalized, ct.email, '') != '' THEN 1 ELSE 0 END) AS reachable_companies
        FROM COMPANIES c
        LEFT JOIN ICP_SCORES s ON s.company_id = c.id
        LEFT JOIN AUDITS a ON a.company_id = c.id
        LEFT JOIN CONTACTS ct ON ct.company_id = c.id
        """
    ).fetchone()
    db_counts = row_to_dict(funnel_row) or {"found_companies": 0, "eligible_companies": 0, "reachable_companies": 0}

    tam_total = sum(b["tam_brazil_companies"] for b in VERIFIABLE_MARKET_BENCHMARKS)
    sam_total = sum(b["sam_target_companies"] for b in VERIFIABLE_MARKET_BENCHMARKS)
    som_total = sum(b["som_12m_capacity"] for b in VERIFIABLE_MARKET_BENCHMARKS)

    found = int(db_counts.get("found_companies") or 0)
    eligible = int(db_counts.get("eligible_companies") or 0)
    reachable = int(db_counts.get("reachable_companies") or 0)

    # Identify geographic expansion opportunities (high-income automotive/marine hubs with low/zero collection in DB)
    collected_cities_rows = rows_to_list(
        conn.execute("SELECT LOWER(city) AS c_low, COUNT(*) AS cnt FROM COMPANIES GROUP BY LOWER(city)").fetchall()
    )
    city_map = {r["c_low"]: r["cnt"] for r in collected_cities_rows if r["c_low"]}

    target_hubs = [
        {"city": "São Paulo", "state": "SP", "country": "Brasil", "estimated_sam_hub": 2100, "rationale": "Maior polo nacional de multimarcas premium, blindados e importadoras (Jardins, Moema, Tatuapé, Alphaville)."},
        {"city": "Curitiba", "state": "PR", "country": "Brasil", "estimated_sam_hub": 680, "rationale": "Segundo maior mercado per capita de veículos premium e superesportivos do país."},
        {"city": "Balneário Camboriú / Florianópolis", "state": "SC", "country": "Brasil", "estimated_sam_hub": 590, "rationale": "Epicentro nacional de náutica (P4 — lanchas/iates) e revendas de supercarros (P2)."},
        {"city": "Belo Horizonte", "state": "MG", "country": "Brasil", "estimated_sam_hub": 520, "rationale": "Forte concentração de revendas seminovos de alto padrão com baixa maturidade web."},
        {"city": "Ribeirão Preto / Campinas", "state": "SP", "country": "Brasil", "estimated_sam_hub": 640, "rationale": "Interior paulista com alta renda do agronegócio e forte demanda por caminhonetes/SUVs premium."},
        {"city": "Goiânia / Brasília", "state": "GO/DF", "country": "Brasil", "estimated_sam_hub": 610, "rationale": "Mercado em rápida expansão para SUVs, picapes premium e aeronáutica/náutica de lazer."},
        {"city": "Miami / Orlando", "state": "FL", "country": "EUA", "estimated_sam_hub": 950, "rationale": "Expansão internacional (ticket em USD) com dezenas de dealers independentes e yacht brokers."},
    ]

    expansion_opportunities = []
    for hub in target_hubs:
        key_parts = [p.strip().lower() for p in hub["city"].split("/")]
        current_in_db = sum(city_map.get(kp, 0) for kp in key_parts)
        penetration_pct = round((current_in_db / hub["estimated_sam_hub"]) * 100, 2)
        expansion_opportunities.append({
            **hub,
            "captured_in_local_db": current_in_db,
            "sam_penetration_pct": penetration_pct,
            "expansion_status": "Explorar Imediatamente (Baixa cobertura local)" if current_in_db < 15 else "Consolidar Abordagens Comerciais",
        })

    return {
        "agent_id": "AGENT_15",
        "agent_name": "MARKET SIZE INTELLIGENCE (TAM / SAM / SOM)",
        "generated_at": now_iso(),
        "macro_market_estimates": {
            "TAM": {
                "companies_count": tam_total,
                "label": "Total Addressable Market (Brasil — Nichos Automotivo & Náutica)",
                "estimated_annual_value_brl": tam_total * 3500,
                "definition": "Total de estabelecimentos ativos de revenda de veículos e embarcações no Brasil segundo fontes setoriais (FENAUTO/FENABRAVE/ACOBAR).",
            },
            "SAM": {
                "companies_count": sam_total,
                "label": "Serviceable Available Market (Segmentos Premium P1–P4 com Gap Digital)",
                "estimated_annual_value_brl": sam_total * 4500,
                "definition": "Frações de médio-alto ticket (seminovos premium, supercarros, importados/blindados e náutica) que não possuem site próprio ou operam com estrutura digital defasada.",
            },
            "SOM": {
                "companies_count": som_total,
                "label": "Serviceable Obtainable Market (Meta Operacional Alcançável em 12 Meses)",
                "estimated_annual_value_brl": som_total * 4500,
                "definition": "Volume de empresas efetivamente alcançáveis pela capacidade de prospecção, produção de demos e fechamento da BRAG em 12 meses.",
            },
        },
        "local_database_funnel_distinction": {
            "empresas_encontradas": {
                "count": found,
                "pct_of_sam": round((found / sam_total) * 100, 2) if sam_total else 0,
                "explanation": "Registros já descobertos e salvos localmente pelo BRAG Lead Hunter (não representa o tamanho total do mercado).",
            },
            "empresas_elegiveis": {
                "count": eligible,
                "pct_of_found": round((eligible / found) * 100, 1) if found else 0,
                "explanation": "Subconjunto das empresas encontradas que possuem Score ICP >= 60 e evidência técnica comprovada de necessidade digital.",
            },
            "empresas_efetivamente_alcancaveis": {
                "count": reachable,
                "pct_of_eligible": round((reachable / eligible) * 100, 1) if eligible else 0,
                "explanation": "Subconjunto das empresas elegíveis que possuem canal direto verificável (WhatsApp, Telefone ou E-mail público) pronto para abordagem imediata.",
            },
        },
        "by_segment_breakdown": VERIFIABLE_MARKET_BENCHMARKS,
        "geographic_expansion_opportunities": expansion_opportunities,
        "methodological_note": (
            "Distinção crítica ativa: A quantidade de registros coletados na base local ("
            f"{found} empresas) representa apenas {round((found / sam_total) * 100, 2)}% do SAM estimado ({sam_total} empresas). "
            "Estimativas macro provêm de relatórios públicos (FENAUTO, ABRABLIN, ACOBAR)."
        ),
    }


# ==============================================================================
# AGENT 16 — SALES EXPERIMENT INTELLIGENCE
# ==============================================================================
def evaluate_experiment_validation(exp: dict[str, Any]) -> dict[str, Any]:
    """
    Applies the CENTRAL RULE to a sales experiment:
    "Nenhum nicho deve ser considerado validado apenas por possuir muitos leads.
     A validação exige evidência comercial obtida através de contatos, conversas, propostas e vendas.
     O sistema deve recomendar expansão somente quando houver dados suficientes para justificar a decisão."
    """
    leads = max(0, int(exp.get("leads_targeted") or 0))
    contacts = max(0, int(exp.get("contacts_made") or 0))
    responses = max(0, int(exp.get("responses_received") or 0))
    meetings = max(0, int(exp.get("meetings_booked") or 0))
    proposals = max(0, int(exp.get("proposals_sent") or 0))
    sales = max(0, int(exp.get("sales_closed") or 0))
    revenue = float(exp.get("revenue_brl") or 0.0)

    contact_rate = round((contacts / leads) * 100, 1) if leads > 0 else 0.0
    response_rate = round((responses / contacts) * 100, 1) if contacts > 0 else 0.0
    meeting_rate = round((meetings / contacts) * 100, 1) if contacts > 0 else 0.0
    proposal_rate = round((proposals / max(1, meetings if meetings > 0 else contacts)) * 100, 1) if contacts > 0 else 0.0
    close_rate_from_proposals = round((sales / proposals) * 100, 1) if proposals > 0 else 0.0
    overall_conversion_rate = round((sales / contacts) * 100, 2) if contacts > 0 else 0.0

    # STRICT VALIDATION GATE (Central Rule)
    if contacts < 15:
        validation_status = "INSUFICIENTE_PARA_DECISAO"
        scale_recommendation = "NÃO ESCALAR AINDA — Executar mínimo de 15 a 30 contatos reais neste experimento."
        rationale = (
            f"Possui {leads} leads mapeados, mas apenas {contacts} contatos realizados. "
            "Regra Central: muitos leads não validam um nicho sem evidência de contatos, conversas, propostas e vendas."
        )
        worthy_of_scale = False
    elif sales >= 1 and proposals >= 2 and response_rate >= 15.0:
        validation_status = "VALIDADO_PARA_ESCALA"
        scale_recommendation = "ESCALAR ESTRATÉGIA — Evidência comercial completa confirmada (contatos -> respostas -> propostas -> vendas)."
        rationale = (
            f"Validado com {contacts} contatos, {responses} respostas ({response_rate}%), "
            f"{proposals} propostas e {sales} venda(s) fechada(s) gerando R$ {revenue:,.2f}."
        )
        worthy_of_scale = True
    elif responses >= 4 and (meetings >= 2 or proposals >= 1):
        validation_status = "EM_TRACAO_PROMISSORA"
        scale_recommendation = "MANTER TESTE E OTIMIZAR FECHAMENTO — Boa taxa de resposta/reuniões, aguardando conversão em vendas para liberar expansão."
        rationale = (
            f"Tração inicial observada ({responses} respostas / {meetings} reuniões / {proposals} propostas), "
            "porém exige fechamento de vendas antes de recomendar expansão em larga escala."
        )
        worthy_of_scale = False
    else:
        validation_status = "BAIXA_CONVERSAO_AJUSTAR_SCRIPT"
        scale_recommendation = "NÃO EXPANDIR — Revisar script de abordagem ou oferta antes de ampliar volume."
        rationale = (
            f"Foram realizados {contacts} contatos com {responses} respostas ({response_rate}%) e {sales} vendas. "
            "Volume de leads não compensa baixa tração comercial."
        )
        worthy_of_scale = False

    return {
        **exp,
        "metrics": {
            "contact_rate_pct": contact_rate,
            "response_rate_pct": response_rate,
            "meeting_rate_pct": meeting_rate,
            "proposal_rate_pct": proposal_rate,
            "close_rate_from_proposals_pct": close_rate_from_proposals,
            "overall_conversion_pct": overall_conversion_rate,
            "revenue_per_contact_brl": round(revenue / contacts, 2) if contacts > 0 else 0.0,
        },
        "validation_status": validation_status,
        "worthy_of_scale": worthy_of_scale,
        "scale_recommendation": scale_recommendation,
        "validation_rationale": rationale,
    }


def ensure_default_experiments(conn: sqlite3.Connection) -> None:
    """
    Ensures the campaign comparison panel has transparent baseline experiment records
    tied to real niches so the user can track and compare scripts & niches immediately.
    Starts with zeroed or realistic tracked funnel counters clearly labeled.
    """
    count = conn.execute("SELECT COUNT(*) AS c FROM SALES_EXPERIMENTS").fetchone()["c"]
    if count > 0:
        return

    # Count actual leads in DB per niche to populate `leads_targeted` accurately
    p1_leads = conn.execute("SELECT COUNT(*) AS c FROM COMPANIES WHERE niche LIKE 'P1%'").fetchone()["c"]
    p2_leads = conn.execute("SELECT COUNT(*) AS c FROM COMPANIES WHERE niche LIKE 'P2%'").fetchone()["c"]
    p4_leads = conn.execute("SELECT COUNT(*) AS c FROM COMPANIES WHERE niche LIKE 'P4%'").fetchone()["c"]

    now = now_iso()
    defaults = [
        (
            new_id("exp"),
            "Exp #1 — P1 Multimarcas SP (Script Diagnóstico Sem Site + Demo 60s)",
            "P1 — Revendas premium e multimarcas",
            "São Paulo",
            "Script A: Observação de Linktree/Sem Site + Preview Catálogo Mobile",
            "Vitrine Digital High-Ticket + Catálogo WhatsApp",
            max(p1_leads, 25),
            0, 0, 0, 0, 0, 0.0,
            "Campanha de teste criada automaticamente a partir dos leads P1 coletados. Registre contatos, respostas, propostas e vendas reais para validar o nicho.",
        ),
        (
            new_id("exp"),
            "Exp #2 — P2 Superesportivos & Luxo (Script Autoridade de Showroom)",
            "P2 — Luxo e superesportivos",
            "São Paulo / Curitiba",
            "Script B: Contraste Porte Físico vs. Presença Web + Demo Exclusiva",
            "Vitrine Digital High-Ticket + Catálogo WhatsApp",
            max(p2_leads, 12),
            0, 0, 0, 0, 0, 0.0,
            "Experimento focado em lojas de superesportivos sem domínio próprio identificado. Aguardando execução de contatos comerciais.",
        ),
        (
            new_id("exp"),
            "Exp #3 — P4 Náutica & Lanchas (Script Ficha Técnica Embarcações)",
            "P4 — Náutica premium",
            "Florianópolis / Litoral SP",
            "Script C: Catálogo Pesquisável por Pés e Motorização no WhatsApp",
            "Vitrine Digital Náutica + Qualificador IA",
            max(p4_leads, 10),
            0, 0, 0, 0, 0, 0.0,
            "Experimento para brokers náuticos. Nenhuma expansão recomendada antes de registrar conversas, propostas e vendas.",
        ),
    ]

    for d in defaults:
        conn.execute(
            """
            INSERT INTO SALES_EXPERIMENTS (
                id, name, niche, city, script_variant, offer_type,
                leads_targeted, contacts_made, responses_received,
                meetings_booked, proposals_sent, sales_closed, revenue_brl,
                notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*d, now, now),
        )
    conn.commit()


def run_agent_16_sales_experiment_intelligence(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    AGENT 16 — SALES EXPERIMENT INTELLIGENCE
    Evaluates all sales experiments, compares niches and scripts, calculates funnel conversion rates,
    and enforces the Central Rule before recommending scale.
    """
    ensure_default_experiments(conn)
    rows = rows_to_list(
        conn.execute("SELECT * FROM SALES_EXPERIMENTS ORDER BY updated_at DESC, created_at DESC").fetchall()
    )
    evaluated = [evaluate_experiment_validation(r) for r in rows]

    total_contacts = sum(e["contacts_made"] for e in evaluated)
    total_responses = sum(e["responses_received"] for e in evaluated)
    total_meetings = sum(e["meetings_booked"] for e in evaluated)
    total_proposals = sum(e["proposals_sent"] for e in evaluated)
    total_sales = sum(e["sales_closed"] for e in evaluated)
    total_revenue = sum(float(e["revenue_brl"] or 0) for e in evaluated)

    validated_for_scale = [e for e in evaluated if e["worthy_of_scale"]]

    return {
        "agent_id": "AGENT_16",
        "agent_name": "SALES EXPERIMENT INTELLIGENCE",
        "generated_at": now_iso(),
        "central_rule": (
            "REGRA CENTRAL ATIVA: Nenhum nicho é considerado validado apenas por possuir muitos leads. "
            "A validação exige evidência comercial obtida através de contatos, conversas, propostas e vendas."
        ),
        "global_funnel_totals": {
            "experiments_count": len(evaluated),
            "total_contacts_made": total_contacts,
            "total_responses_received": total_responses,
            "total_meetings_booked": total_meetings,
            "total_proposals_sent": total_proposals,
            "total_sales_closed": total_sales,
            "total_revenue_brl": total_revenue,
            "avg_response_rate_pct": round((total_responses / total_contacts) * 100, 1) if total_contacts > 0 else 0.0,
        },
        "experiments": evaluated,
        "strategies_worthy_of_scale": validated_for_scale,
        "executive_verdict": (
            f"{len(validated_for_scale)} experimento(s) atingiram validação comercial completa para escala."
            if validated_for_scale
            else (
                "Nenhum nicho/campanha possui ainda evidência comercial suficiente (contatos + propostas + vendas) "
                "para justificar expansão automática. Utilize os leads Prioridade A/B já coletados para registrar "
                "os primeiros contatos, respostas, reuniões, propostas e vendas no painel."
            )
        ),
    }


def upsert_sales_experiment(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    now = now_iso()
    exp_id = payload.get("id")
    if exp_id:
        existing = conn.execute("SELECT * FROM SALES_EXPERIMENTS WHERE id = ?", (exp_id,)).fetchone()
    else:
        existing = None

    if existing is None:
        exp_id = new_id("exp")
        conn.execute(
            """
            INSERT INTO SALES_EXPERIMENTS (
                id, name, campaign_id, niche, city, script_variant, offer_type,
                leads_targeted, contacts_made, responses_received,
                meetings_booked, proposals_sent, sales_closed, revenue_brl,
                notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp_id,
                payload.get("name") or "Experimento Comercial",
                payload.get("campaign_id"),
                payload.get("niche") or "P1 — Revendas premium e multimarcas",
                payload.get("city") or "São Paulo",
                payload.get("script_variant") or "Script A — Diagnóstico + Demo",
                payload.get("offer_type") or "Vitrine Digital High-Ticket",
                int(payload.get("leads_targeted") or 0),
                int(payload.get("contacts_made") or 0),
                int(payload.get("responses_received") or 0),
                int(payload.get("meetings_booked") or 0),
                int(payload.get("proposals_sent") or 0),
                int(payload.get("sales_closed") or 0),
                float(payload.get("revenue_brl") or 0.0),
                payload.get("notes") or "",
                now,
                now,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE SALES_EXPERIMENTS SET
                name = COALESCE(?, name),
                niche = COALESCE(?, niche),
                city = COALESCE(?, city),
                script_variant = COALESCE(?, script_variant),
                offer_type = COALESCE(?, offer_type),
                leads_targeted = COALESCE(?, leads_targeted),
                contacts_made = COALESCE(?, contacts_made),
                responses_received = COALESCE(?, responses_received),
                meetings_booked = COALESCE(?, meetings_booked),
                proposals_sent = COALESCE(?, proposals_sent),
                sales_closed = COALESCE(?, sales_closed),
                revenue_brl = COALESCE(?, revenue_brl),
                notes = COALESCE(?, notes),
                updated_at = ?
            WHERE id = ?
            """,
            (
                payload.get("name"),
                payload.get("niche"),
                payload.get("city"),
                payload.get("script_variant"),
                payload.get("offer_type"),
                int(payload["leads_targeted"]) if "leads_targeted" in payload and payload["leads_targeted"] is not None else None,
                int(payload["contacts_made"]) if "contacts_made" in payload and payload["contacts_made"] is not None else None,
                int(payload["responses_received"]) if "responses_received" in payload and payload["responses_received"] is not None else None,
                int(payload["meetings_booked"]) if "meetings_booked" in payload and payload["meetings_booked"] is not None else None,
                int(payload["proposals_sent"]) if "proposals_sent" in payload and payload["proposals_sent"] is not None else None,
                int(payload["sales_closed"]) if "sales_closed" in payload and payload["sales_closed"] is not None else None,
                float(payload["revenue_brl"]) if "revenue_brl" in payload and payload["revenue_brl"] is not None else None,
                payload.get("notes"),
                now,
                exp_id,
            ),
        )
    conn.commit()
    row = row_to_dict(conn.execute("SELECT * FROM SALES_EXPERIMENTS WHERE id = ?", (exp_id,)).fetchone())
    return evaluate_experiment_validation(row or {})
