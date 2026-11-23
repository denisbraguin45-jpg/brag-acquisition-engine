"""
Commercial Intelligence & Opportunity Intelligence Engine (Sections 4 & 5).

Section 4 — Scoring Engine (Max 100 points):
- Absence of website: 25 points (or third-party/WhatsApp-only without own site: 22-25 points)
- Broken or very outdated website: up to 20 points
- High-value services: up to 15 points
- Commercial reputation: up to 10 points
- Active commercial Instagram: up to 10 points
- Commercial contact available: up to 10 points
- Investment potential (based strictly on observable public signals, never inventing financials): up to 10 points

Classification:
- A: 80–100
- B: 60–79
- C: 40–59
- D: below 40

Explicit Separation:
- ICP Fit (`icp_fit_status`)
- Data Quality (`data_quality_level`)
- Need Evidence (`need_evidence_level`)
- Confirmed Purchase Intent (`confirmed_purchase_intent`)

Section 5 — Opportunity Intelligence:
Generates automated, evidence-backed analysis for each company:
- Diagnosis (bulleted facts found)
- Opportunity (concrete digital product solution)
- Commercial Argument / Pitch (personalized hook based on observed facts)
- Recommended Next Action
"""
import json
import re
import sqlite3
from typing import Any, Optional

from backend.database import new_id, now_iso, row_to_dict
from backend.deduplication import strip_accents

HIGH_VALUE_KEYWORDS = re.compile(
    r"\b(premium|luxo|superesportiv|supercar|exotic|ferrari|lamborghini|porsche|mclaren|"
    r"bmw|mercedes|audi|land rover|range rover|jaguar|volvo|blindad|importad|"
    r"lancha|iate|yacht|jetski|sea[- ]?doo|embarcacoes|nautica|multimarcas|seminovos)\b",
    re.I,
)

ULTRA_HIGH_TICKET_KEYWORDS = re.compile(
    r"\b(ferrari|lamborghini|mclaren|porsche|blindad|iate|yacht|lancha|importad|superesportiv|rolls[- ]?royce|bentley)\b",
    re.I,
)

PREMIUM_LOCATIONS = re.compile(
    r"\b(sao paulo|sp|alphaville|jardins|moema|itaim|morumbi|campinas|curitiba|florianopolis|"
    r"balneario camboriu|itapema|porto alegre|belo horizonte|brasilia|lago sul|goiania|miami|orlando|florida)\b",
    re.I,
)


def classify_priority(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def evaluate_company_intelligence(
    company: dict[str, Any],
    contact: Optional[dict[str, Any]] = None,
    social: Optional[dict[str, Any]] = None,
    website: Optional[dict[str, Any]] = None,
    audit: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Pure, deterministic scoring and opportunity diagnosis function.
    """
    contact = contact or {}
    social = social or {}
    website = website or {}
    audit = audit or {}

    justifications: list[dict[str, Any]] = []
    diagnosis_points: list[str] = []

    name = company.get("name") or "Empresa"
    niche = company.get("niche") or ""
    subniche = company.get("subniche") or ""
    category = company.get("category") or ""
    city = company.get("city") or ""
    state = company.get("state") or ""
    has_own_site = bool(company.get("has_own_website") or website.get("is_own_domain"))
    audit_status = audit.get("audit_status") or ("adequate" if has_own_site else "no_site")

    try:
        services = json.loads(company.get("services_offered") or "[]") if isinstance(company.get("services_offered"), str) else (company.get("services_offered") or [])
    except Exception:
        services = []

    try:
        audit_issues = json.loads(audit.get("issues_found") or "[]") if isinstance(audit.get("issues_found"), str) else (audit.get("issues_found") or [])
    except Exception:
        audit_issues = []

    # ---------------------------------------------------------
    # CRITERION 1: Ausência de website (25 pts) OU Website quebrado/ultrapassado (até 20 pts)
    # Note: A company either lacks an official website (up to 25 pts) OR has a website that is broken/outdated (up to 20 pts).
    # ---------------------------------------------------------
    pts_no_website = 0
    pts_broken_website = 0

    link_cat = website.get("link_category") or ""
    link_type = website.get("link_type") or ""

    if not has_own_site:
        pts_no_website = 25
        if link_cat in ("terceiro", "whatsapp") or link_type:
            pts_broken_website = 15
            reason_site = f"Não possui website oficial próprio: +25/25 pts"
            reason_broken = f"Estrutura digital improvisada/ultrapassada ({link_type or 'apenas link externo sem catálogo'}): +15/20 pts"
            diagnosis_points.append(f"Não foi identificado website oficial próprio (opera com {link_type or 'link externo'}).")
        else:
            pts_broken_website = 18
            reason_site = "Ausência verificada de website oficial próprio: +25/25 pts"
            reason_broken = "Dependência total de redes sociais sem vitrine digital nem página de captura: +18/20 pts"
            diagnosis_points.append("Não foi identificado website oficial próprio.")
        justifications.append({
            "criterion": "Ausência de website",
            "points": pts_no_website,
            "max_points": 25,
            "reason": reason_site,
        })
        justifications.append({
            "criterion": "Website quebrado ou ultrapassado",
            "points": pts_broken_website,
            "max_points": 20,
            "reason": reason_broken,
        })
    else:
        justifications.append({
            "criterion": "Ausência de website",
            "points": 0,
            "max_points": 25,
            "reason": f"Possui domínio próprio identificado ({website.get('domain') or website.get('url') or 'ativo'}): +0/25 pts",
        })
        if audit_status == "broken" or not audit.get("http_available", True):
            pts_broken_website = 20
            reason_broken = f"Website próprio fora do ar ou com erro HTTP ({audit.get('http_status') or 'falha de conexão'}): +20/20 pts"
            diagnosis_points.append(f"Possui domínio registrado, porém o website está quebrado/indisponível ({ '; '.join(audit_issues[:2]) or 'erro HTTP' }).")
        elif audit_status in ("weak", "needs_improvement") or len(audit_issues) > 0:
            raw_b = min(20, len(audit_issues) * 5)
            if not audit.get("has_https", True):
                raw_b = max(raw_b, 14)
            if not audit.get("is_responsive", True):
                raw_b = max(raw_b, 16)
            if (audit.get("commercial_structure_score") or 0) < 50:
                raw_b = max(raw_b, 12)
            pts_broken_website = min(20, max(6, raw_b))
            reason_broken = f"Website apresenta falhas técnicas/comerciais ({'; '.join(audit_issues[:3])}): +{pts_broken_website}/20 pts"
            diagnosis_points.append(f"Possui website próprio com defasagens verificadas: {'; '.join(audit_issues[:3])}.")
        else:
            pts_broken_website = 0
            reason_broken = "Website próprio funcional, responsivo e com estrutura adequada: +0/20 pts"
            diagnosis_points.append("Possui website oficial ativo e tecnicamente funcional.")

        justifications.append({
            "criterion": "Website quebrado ou ultrapassado",
            "points": pts_broken_website,
            "max_points": 20,
            "reason": reason_broken,
        })

    # ---------------------------------------------------------
    # CRITERION 3: Serviços de alto valor (até 15 pts)
    # ---------------------------------------------------------
    full_service_text = strip_accents(
        f"{niche} {subniche} {category} {' '.join(services)} {social.get('biography') or ''} {name}"
    ).lower()
    pts_high_value = 0
    if ULTRA_HIGH_TICKET_KEYWORDS.search(full_service_text) or "p2" in niche.lower() or "p4" in niche.lower() or "p3" in niche.lower() or "p1" in niche.lower():
        pts_high_value = 15
        hv_reason = f"Opera com produtos/serviços de alto ticket ({', '.join(services[:3]) or niche}): +15/15 pts"
        diagnosis_points.append(f"Trabalha com operação de alto valor ({', '.join(services[:3]) or niche}).")
    elif HIGH_VALUE_KEYWORDS.search(full_service_text):
        pts_high_value = 14
        hv_reason = f"Atua em segmento comercial de alto valor agregado ({niche or category}): +14/15 pts"
        diagnosis_points.append(f"Atua no segmento de {niche or category} com ticket elevado.")
    elif services or niche:
        pts_high_value = 9
        hv_reason = f"Serviços comerciais identificados ({', '.join(services[:2]) or niche}): +9/15 pts"
        diagnosis_points.append(f"Oferece serviços comerciais em {niche or category}.")
    else:
        hv_reason = "Serviços específicos de alto valor não confirmados nos dados públicos: +0/15 pts"

    justifications.append({
        "criterion": "Serviços de alto valor",
        "points": pts_high_value,
        "max_points": 15,
        "reason": hv_reason,
    })

    # ---------------------------------------------------------
    # CRITERION 4: Reputação comercial (até 10 pts)
    # ---------------------------------------------------------
    pts_reputation = 0
    rating = company.get("google_rating")
    reviews = company.get("google_reviews_count")
    followers = social.get("followers_count")
    posts_count = social.get("posts_count")
    bio_text = social.get("biography") or ""

    rep_parts = []
    if rating is not None:
        r_val = float(rating)
        rev_val = int(reviews or 0)
        if r_val >= 4.5 and rev_val >= 20:
            pts_reputation = 10
        elif r_val >= 4.0 and rev_val >= 8:
            pts_reputation = 8
        elif r_val >= 3.5:
            pts_reputation = 6
        rep_parts.append(f"Nota Google {r_val:.1f} ({rev_val} avaliações)")
        diagnosis_points.append(f"Possui reputação pública no Google com nota {r_val:.1f} e {rev_val} avaliações.")

    if followers is not None and int(followers) > 0:
        f_val = int(followers)
        ig_rep = 10 if f_val >= 8000 else (8 if f_val >= 2000 else (6 if f_val >= 400 else 4))
        if ig_rep > pts_reputation:
            pts_reputation = ig_rep
        rep_parts.append(f"{f_val:,} seguidores no Instagram".replace(",", "."))
        if rating is None:
            diagnosis_points.append(f"Reputação digital sustentada por audiência comercial de {f_val:,} seguidores.".replace(",", "."))

    # Check tradition/years in market mentioned in bio
    years_m = re.search(r"\b(\d{1,2})\s*anos\s+de\s+(tradi[cç][aã]o|mercado|hist[oó]ria|experi[eê]ncia)\b", bio_text, re.I)
    if years_m and pts_reputation < 10:
        pts_reputation = min(10, pts_reputation + 3)
        rep_parts.append(f"{years_m.group(1)} anos de atuação informados na bio")

    if not rep_parts and (company.get("address") or company.get("opening_hours")):
        pts_reputation = 5
        rep_parts.append("Estabelecimento físico com endereço comercial verificável")
        diagnosis_points.append("Estabelecimento comercial com endereço físico público identificado.")

    justifications.append({
        "criterion": "Reputação comercial",
        "points": pts_reputation,
        "max_points": 10,
        "reason": f"{' + '.join(rep_parts)}: +{pts_reputation}/10 pts" if rep_parts else "Sem avaliações ou indicadores públicos de reputação coletados: +0/10 pts",
    })

    # ---------------------------------------------------------
    # CRITERION 5: Instagram comercial ativo (até 10 pts)
    # ---------------------------------------------------------
    pts_instagram = 0
    ig_username = social.get("username") or ""
    latest_post = social.get("latest_post_date") or ""
    if ig_username or company.get("has_instagram"):
        pts_instagram = 6
        ig_details = [f"@{ig_username}" if ig_username else "Perfil ativo"]
        if posts_count is not None and int(posts_count) >= 15:
            pts_instagram += 2
            ig_details.append(f"{posts_count} publicações")
        if latest_post or "estoque" in (social.get("activity_indicators") or "").lower() or (followers is not None and int(followers) >= 500):
            pts_instagram += 2
            if latest_post:
                ig_details.append(f"últ. post {latest_post}")
        pts_instagram = min(10, pts_instagram)
        diagnosis_points.append(f"Possui Instagram comercial ativo ({', '.join(ig_details)}).")
        ig_reason = f"Instagram comercial ativo ({', '.join(ig_details)}): +{pts_instagram}/10 pts"
    else:
        ig_reason = "Instagram comercial não identificado: +0/10 pts"

    justifications.append({
        "criterion": "Instagram comercial ativo",
        "points": pts_instagram,
        "max_points": 10,
        "reason": ig_reason,
    })

    # ---------------------------------------------------------
    # CRITERION 6: Contato comercial disponível (até 10 pts)
    # ---------------------------------------------------------
    pts_contact = 0
    wpp = contact.get("whatsapp") or ""
    phone = contact.get("phone_normalized") or contact.get("phone_raw") or ""
    email = contact.get("email") or ""
    c_channels = []
    if wpp:
        pts_contact += 7
        c_channels.append(f"WhatsApp ({wpp})")
    elif phone:
        pts_contact += 6
        c_channels.append(f"Telefone ({phone})")

    if email:
        pts_contact += 4
        c_channels.append(f"E-mail ({email})")

    if c_channels and (contact.get("whatsapp_verified") or len(c_channels) >= 2):
        pts_contact = 10
    elif c_channels:
        pts_contact = max(pts_contact, 8)
    elif ig_username and ("whatsapp" in (website.get("link_category") or "") or "terceiro" in (website.get("link_category") or "")):
        pts_contact = 7
        c_channels.append(f"Link comercial na bio (@{ig_username})")
    elif ig_username:
        pts_contact = 5
        c_channels.append(f"Direct comercial (@{ig_username})")

    pts_contact = min(10, pts_contact)
    if c_channels:
        diagnosis_points.append(f"Canais de contato direto disponíveis: {', '.join(c_channels)}.")
        contact_reason = f"Contatos verificados ({', '.join(c_channels)}): +{pts_contact}/10 pts"
    else:
        contact_reason = "Nenhum telefone, WhatsApp ou e-mail público encontrado: +0/10 pts"

    justifications.append({
        "criterion": "Contato comercial disponível",
        "points": pts_contact,
        "max_points": 10,
        "reason": contact_reason,
    })

    # ---------------------------------------------------------
    # CRITERION 7: Potencial de investimento (até 10 pts)
    # Strictly derived from observable public operational signals (never inventing revenue).
    # ---------------------------------------------------------
    pts_investment = 0
    inv_signals = []
    loc_str = strip_accents(f"{city} {state} {company.get('address') or ''}").lower()
    if PREMIUM_LOCATIONS.search(loc_str):
        pts_investment += 4
        inv_signals.append(f"localização em polo comercial ({city or state})")
    if pts_high_value >= 13:
        pts_investment += 4
        inv_signals.append("estoque/serviços de alto ticket unitário")
    if (posts_count is not None and int(posts_count) >= 30) or (followers is not None and int(followers) >= 1000) or (reviews is not None and int(reviews) >= 15) or "conta comercial" in (social.get("activity_indicators") or "").lower():
        pts_investment += 2
        inv_signals.append("volume operacional ativo")
    pts_investment = min(10, pts_investment)

    inv_reason = (
        f"Sinais operacionais públicos ({', '.join(inv_signals)} — sem estimativa financeira inventada): +{pts_investment}/10 pts"
        if inv_signals
        else "Sinais públicos de porte operacional limitados: +0/10 pts"
    )
    justifications.append({
        "criterion": "Potencial de investimento",
        "points": pts_investment,
        "max_points": 10,
        "reason": inv_reason,
    })

    total_score = min(
        100,
        pts_no_website
        + pts_broken_website
        + pts_high_value
        + pts_reputation
        + pts_instagram
        + pts_contact
        + pts_investment,
    )
    priority_class = classify_priority(total_score)

    # ---------------------------------------------------------
    # SEPARATION OF DIMENSIONS (Section 4)
    # ---------------------------------------------------------
    if pts_high_value >= 12 and pts_investment >= 6:
        icp_fit_status = "Alta aderência ao ICP BRAG (Alto Ticket + Operação Ativa)"
    elif pts_high_value >= 8:
        icp_fit_status = "Média aderência ao ICP BRAG (Nicho compatível)"
    else:
        icp_fit_status = "Baixa aderência ao ICP (Verificar operação manualmente)"

    completeness = sum([
        1 if name else 0,
        1 if city else 0,
        1 if (wpp or phone or email) else 0,
        1 if (ig_username or has_own_site) else 0,
        1 if (services or niche) else 0,
    ])
    if completeness >= 4:
        data_quality_level = "Alta (Fontes verificadas + Contato + Canal digital auditado)"
    elif completeness == 3:
        data_quality_level = "Média (Dados comerciais essenciais presentes)"
    else:
        data_quality_level = "Baixa (Requer enriquecimento adicional de contato)"

    if pts_no_website >= 20:
        need_evidence_level = f"Forte — Empresa opera sem website próprio ({link_type or 'apenas redes sociais/agregador'})"
    elif pts_broken_website >= 12:
        need_evidence_level = f"Forte — Website próprio com problemas técnicos/comerciais ({'; '.join(audit_issues[:2])})"
    elif pts_broken_website > 0:
        need_evidence_level = "Moderada — Website funcional, mas com oportunidades de otimização de conversão"
    else:
        need_evidence_level = "Baixa — Website próprio ativo e estruturado"

    confirmed_purchase_intent = "Não confirmada (evidência técnica de necessidade detectada; intenção requer abordagem comercial)"

    # ---------------------------------------------------------
    # SECTION 5: OPPORTUNITY INTELLIGENCE (Diagnosis, Opportunity, Pitch, Next Action)
    # ---------------------------------------------------------
    is_nautic = "p4" in niche.lower() or "nautic" in full_service_text or "lancha" in full_service_text
    asset_label = "embarcações e lanchas" if is_nautic else "veículos e estoque"

    if not has_own_site:
        opportunity_text = (
            f"Desenvolver uma vitrine digital própria para {name} com catálogo estruturado de {asset_label}, "
            f"filtros inteligentes de busca, página de detalhes com integração direta ao WhatsApp e captação ativa de interessados."
        )
        recommended_offer = "Vitrine Digital High-Ticket + Catálogo Inteligente + Automação WhatsApp"
        hook_gap = (
            f"notei que a {name} movimenta um excelente acervo em {city or 'sua região'} pelo Instagram, "
            f"mas hoje direciona os clientes para {link_type.lower() if link_type else 'fora de um domínio próprio'}, "
            f"sem uma vitrine oficial com busca rápida de {asset_label}."
        )
    elif audit_status == "broken":
        opportunity_text = (
            f"Reconstruir o website oficial da {name} (atualmente indisponível/com falha HTTP) em infraestrutura moderna "
            f"de alta velocidade, com certificado SSL, catálogo mobile-first de {asset_label} e botão de conversão no WhatsApp."
        )
        recommended_offer = "Rebuild Completo de Website + Catálogo Mobile-First + Recuperação de Tráfego"
        hook_gap = (
            f"ao acessar o site oficial da {name} ({website.get('domain') or 'domínio atual'}), identifiquei que a página "
            f"está apresentando falha de carregamento ({audit_issues[0] if audit_issues else 'erro HTTP'}), o que faz clientes "
            f"qualificados desistirem antes de chamar no WhatsApp."
        )
    elif pts_broken_website > 0:
        top_issues_str = ", ".join(audit_issues[:2]).lower() if audit_issues else "oportunidades de melhoria mobile e conversão"
        opportunity_text = (
            f"Modernizar a presença web da {name} corrigindo {top_issues_str}, implementando layout mobile-first "
            f"de alta performance (PageSpeed ≥ 95), CTAs claros e funil direto para WhatsApp."
        )
        recommended_offer = "Redesign de Conversão + Otimização Mobile & Captação WhatsApp"
        hook_gap = (
            f"analisei a presença digital da {name} e vi que, embora já possuam site ({website.get('domain')}), "
            f"existem pontos técnicos travando conversões no celular ({top_issues_str})."
        )
    else:
        opportunity_text = (
            f"Implementar camada complementar de automação comercial com IA no WhatsApp e landing pages dedicadas "
            f"para campanhas de tráfego pago de {asset_label}."
        )
        recommended_offer = "Automação de Atendimento IA + Landing Pages de Alta Conversão"
        hook_gap = (
            f"vi que a {name} já conta com estrutura web ativa em {city or 'sua região'} e podemos acelerar "
            f"a qualificação dos leads que chegam do Instagram e Google com automação comercial."
        )

    commercial_pitch = (
        f"Olá, equipe da {name}! Aqui é da BRAG International. Acompanhando o posicionamento de vocês em {city or 'seu mercado'}, "
        f"{hook_gap} Nós preparamos uma estrutura demonstrativa sob medida para o padrão da {name}, "
        f"focada em apresentar seu catálogo com autoridade e levar o comprador direto para o WhatsApp da loja. "
        f"Posso enviar o link de demonstração em 60 segundos para vocês avaliarem?"
    )

    best_channel = "WhatsApp" if wpp else ("Telefone" if phone else ("E-mail" if email else "Instagram Direct"))
    if priority_class == "A":
        recommended_next_action = (
            f"PRIORIDADE MÁXIMA (Classe A): Preparar demonstração visual rápida e abordar decisor via {best_channel} "
            f"apresentando o diagnóstico e o ganho imediato de autoridade e captação."
        )
    elif priority_class == "B":
        recommended_next_action = (
            f"ALTA PRIORIDADE (Classe B): Validar contato do responsável comercial e iniciar cadência consultiva via {best_channel} "
            f"com foco nas oportunidades identificadas."
        )
    elif priority_class == "C":
        recommended_next_action = (
            f"PRIORIDADE MODERADA (Classe C): Enriquecer dados faltantes de contato/decisor antes de mobilizar produção de demo."
        )
    else:
        recommended_next_action = (
            "BAIXA PRIORIDADE (Classe D): Manter em arquivo/observação; não alocar tempo de engenharia ou SDR no momento."
        )

    return {
        "total_score": total_score,
        "priority_class": priority_class,
        "pts_no_website": pts_no_website,
        "pts_broken_website": pts_broken_website,
        "pts_high_value_services": pts_high_value,
        "pts_reputation": pts_reputation,
        "pts_active_instagram": pts_instagram,
        "pts_commercial_contact": pts_contact,
        "pts_investment_potential": pts_investment,
        "justifications": justifications,
        "icp_fit_status": icp_fit_status,
        "data_quality_level": data_quality_level,
        "need_evidence_level": need_evidence_level,
        "confirmed_purchase_intent": confirmed_purchase_intent,
        "diagnosis": "\n".join(f"• {d}" for d in diagnosis_points),
        "diagnosis_list": diagnosis_points,
        "opportunity_text": opportunity_text,
        "commercial_pitch": commercial_pitch,
        "recommended_next_action": recommended_next_action,
        "recommended_offer": recommended_offer,
    }


def score_and_save_company(conn: sqlite3.Connection, company_id: str) -> dict[str, Any]:
    """
    Loads company + related records from SQLite, calculates ICP Score & Opportunity Intelligence,
    and upserts into ICP_SCORES.
    """
    comp_row = conn.execute("SELECT * FROM COMPANIES WHERE id = ?", (company_id,)).fetchone()
    if not comp_row:
        raise ValueError(f"Company {company_id} not found")
    company = row_to_dict(comp_row) or {}

    ct_row = conn.execute("SELECT * FROM CONTACTS WHERE company_id = ? LIMIT 1", (company_id,)).fetchone()
    sp_row = conn.execute("SELECT * FROM SOCIAL_PROFILES WHERE company_id = ? LIMIT 1", (company_id,)).fetchone()
    web_row = conn.execute("SELECT * FROM WEBSITES WHERE company_id = ? LIMIT 1", (company_id,)).fetchone()
    aud_row = conn.execute("SELECT * FROM AUDITS WHERE company_id = ? LIMIT 1", (company_id,)).fetchone()

    result = evaluate_company_intelligence(
        company=company,
        contact=row_to_dict(ct_row),
        social=row_to_dict(sp_row),
        website=row_to_dict(web_row),
        audit=row_to_dict(aud_row),
    )

    now = now_iso()
    existing_score = conn.execute("SELECT id FROM ICP_SCORES WHERE company_id = ?", (company_id,)).fetchone()
    just_json = json.dumps(result["justifications"], ensure_ascii=False)

    if existing_score is None:
        conn.execute(
            """
            INSERT INTO ICP_SCORES (
                id, company_id, total_score, priority_class,
                pts_no_website, pts_broken_website, pts_high_value_services,
                pts_reputation, pts_active_instagram, pts_commercial_contact,
                pts_investment_potential, justifications,
                icp_fit_status, data_quality_level, need_evidence_level,
                confirmed_purchase_intent, diagnosis, opportunity_text,
                commercial_pitch, recommended_next_action, recommended_offer, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("icp"),
                company_id,
                result["total_score"],
                result["priority_class"],
                result["pts_no_website"],
                result["pts_broken_website"],
                result["pts_high_value_services"],
                result["pts_reputation"],
                result["pts_active_instagram"],
                result["pts_commercial_contact"],
                result["pts_investment_potential"],
                just_json,
                result["icp_fit_status"],
                result["data_quality_level"],
                result["need_evidence_level"],
                result["confirmed_purchase_intent"],
                result["diagnosis"],
                result["opportunity_text"],
                result["commercial_pitch"],
                result["recommended_next_action"],
                result["recommended_offer"],
                now,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE ICP_SCORES SET
                total_score = ?, priority_class = ?,
                pts_no_website = ?, pts_broken_website = ?, pts_high_value_services = ?,
                pts_reputation = ?, pts_active_instagram = ?, pts_commercial_contact = ?,
                pts_investment_potential = ?, justifications = ?,
                icp_fit_status = ?, data_quality_level = ?, need_evidence_level = ?,
                confirmed_purchase_intent = ?, diagnosis = ?, opportunity_text = ?,
                commercial_pitch = ?, recommended_next_action = ?, recommended_offer = ?, calculated_at = ?
            WHERE company_id = ?
            """,
            (
                result["total_score"],
                result["priority_class"],
                result["pts_no_website"],
                result["pts_broken_website"],
                result["pts_high_value_services"],
                result["pts_reputation"],
                result["pts_active_instagram"],
                result["pts_commercial_contact"],
                result["pts_investment_potential"],
                just_json,
                result["icp_fit_status"],
                result["data_quality_level"],
                result["need_evidence_level"],
                result["confirmed_purchase_intent"],
                result["diagnosis"],
                result["opportunity_text"],
                result["commercial_pitch"],
                result["recommended_next_action"],
                result["recommended_offer"],
                now,
                company_id,
            ),
        )

    return result
