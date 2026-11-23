"""
Export & BRAG CRM REST Integration Module (Sections 8 & 10).
Supports:
- CSV export
- JSON export
- Filtering by minimum score, priority class, niche, city, website presence
- REST API integration with BRAG CRM (`/api/v1/crm/companies/ingest`)
- Export history logging in `EXPORT_HISTORY` table
"""
import csv
import io
import json
import sqlite3
import urllib.error
import urllib.request
from typing import Any, Optional

from backend.config import get_config
from backend.database import new_id, now_iso, row_to_dict, rows_to_list


def query_enriched_leads(
    conn: sqlite3.Connection,
    min_score: Optional[int] = None,
    priority: Optional[str] = None,
    niche: Optional[str] = None,
    city: Optional[str] = None,
    has_website: Optional[str] = None,
    has_instagram: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """
    Returns full enriched lead records joining COMPANIES, CONTACTS, SOCIAL_PROFILES, WEBSITES, AUDITS, and ICP_SCORES.
    """
    where_clauses = ["1=1"]
    params: list[Any] = []

    if min_score is not None:
        where_clauses.append("COALESCE(s.total_score, 0) >= ?")
        params.append(int(min_score))

    if priority and priority.upper() in ("A", "B", "C", "D"):
        where_clauses.append("s.priority_class = ?")
        params.append(priority.upper())

    if niche:
        where_clauses.append("LOWER(c.niche) LIKE ?")
        params.append(f"%{niche.lower()}%")

    if city:
        where_clauses.append("(LOWER(c.city) LIKE ? OR LOWER(c.state) LIKE ?)")
        params.extend([f"%{city.lower()}%", f"%{city.lower()}%"])

    if has_website in ("yes", "true", "1", "com_site"):
        where_clauses.append("c.has_own_website = 1")
    elif has_website in ("no", "false", "0", "sem_site"):
        where_clauses.append("c.has_own_website = 0")

    if has_instagram in ("yes", "true", "1"):
        where_clauses.append("c.has_instagram = 1")
    elif has_instagram in ("no", "false", "0"):
        where_clauses.append("c.has_instagram = 0")

    if search:
        q = f"%{search.lower()}%"
        where_clauses.append(
            "(LOWER(c.name) LIKE ? OR LOWER(COALESCE(sp.username, '')) LIKE ? "
            "OR LOWER(c.city) LIKE ? OR LOWER(COALESCE(ct.phone_raw, '')) LIKE ?)"
        )
        params.extend([q, q, q, q])

    sql = f"""
    SELECT
        c.id,
        c.slug,
        c.name,
        c.country,
        c.state,
        c.city,
        c.region,
        c.address,
        c.niche,
        c.subniche,
        c.category,
        c.services_offered,
        c.google_rating,
        c.google_reviews_count,
        c.opening_hours,
        c.maps_url,
        c.has_own_website,
        c.has_instagram,
        c.commercial_status,
        c.source,
        c.data_confidence,
        c.discovered_at,
        c.updated_at,
        ct.phone_raw AS phone,
        ct.phone_normalized,
        ct.whatsapp,
        ct.whatsapp_verified,
        ct.email,
        ct.contact_page_url,
        sp.username AS instagram_username,
        sp.profile_url AS instagram_url,
        sp.biography AS instagram_bio,
        sp.followers_count,
        sp.posts_count,
        sp.latest_post_date,
        w.url AS website_url,
        w.domain AS website_domain,
        w.link_category,
        w.link_type,
        w.is_own_domain,
        a.http_available,
        a.http_status,
        a.has_https,
        a.load_time_ms,
        a.is_responsive,
        a.presentation_quality_score,
        a.offer_clarity_score,
        a.has_cta,
        a.has_whatsapp_button,
        a.has_contact_form,
        a.commercial_structure_score,
        a.audit_status,
        a.issues_found AS audit_issues,
        a.improvement_opportunities AS audit_opportunities,
        s.total_score AS score,
        s.priority_class AS priority,
        s.pts_no_website,
        s.pts_broken_website,
        s.pts_high_value_services,
        s.pts_reputation,
        s.pts_active_instagram,
        s.pts_commercial_contact,
        s.pts_investment_potential,
        s.justifications,
        s.icp_fit_status,
        s.data_quality_level,
        s.need_evidence_level,
        s.confirmed_purchase_intent,
        s.diagnosis,
        s.opportunity_text,
        s.commercial_pitch,
        s.recommended_next_action,
        s.recommended_offer
    FROM COMPANIES c
    LEFT JOIN CONTACTS ct ON ct.company_id = c.id
    LEFT JOIN SOCIAL_PROFILES sp ON sp.company_id = c.id
    LEFT JOIN WEBSITES w ON w.company_id = c.id
    LEFT JOIN AUDITS a ON a.company_id = c.id
    LEFT JOIN ICP_SCORES s ON s.company_id = c.id
    WHERE {" AND ".join(where_clauses)}
    ORDER BY COALESCE(s.total_score, 0) DESC, c.updated_at DESC
    LIMIT ?
    """
    params.append(int(limit))
    rows = rows_to_list(conn.execute(sql, tuple(params)).fetchall())

    for r in rows:
        for json_col in ("services_offered", "audit_issues", "audit_opportunities", "justifications"):
            raw_val = r.get(json_col)
            if isinstance(raw_val, str) and raw_val:
                try:
                    r[json_col] = json.loads(raw_val)
                except Exception:
                    r[json_col] = []
            elif not raw_val:
                r[json_col] = []
    return rows


def build_brag_crm_payload(lead: dict[str, Any]) -> dict[str, Any]:
    """
    Builds the REST payload required by Section 10 AND compatible with BRAGHIN_IA's
    `/api/v1/crm/companies/ingest` endpoint.
    Contains all 16 required fields from Section 10:
    - Nome da empresa (`name`)
    - Nicho (`niche`)
    - Cidade (`city`)
    - País (`country`)
    - Website (`website` / `websiteOriginal`)
    - Instagram (`instagram`)
    - Telefone (`phone`)
    - WhatsApp (`whatsapp`)
    - E-mail (`email`)
    - Avaliações (`reviews` / `google_rating` + `google_reviews_count`)
    - Score (`score` / `icpScore`)
    - Prioridade (`priority` / `icpTier`)
    - Diagnóstico (`diagnosis` / `icpJustification`)
    - Oportunidade (`opportunity` / `digitalGap`)
    - Fonte (`source`)
    - Data de descoberta (`discoveredAt`)
    """
    ig_handle = lead.get("instagram_username")
    ig_formatted = f"@{ig_handle.lstrip('@')}" if ig_handle else ""
    rating = lead.get("google_rating")
    rev_count = lead.get("google_reviews_count")
    reviews_summary = (
        f"Nota {rating} ({rev_count or 0} avaliações)"
        if rating is not None
        else (f"{lead.get('followers_count')} seguidores IG" if lead.get("followers_count") else "Sem avaliações públicas")
    )

    score_val = int(lead.get("score") or 0)
    priority_val = lead.get("priority") or ("A" if score_val >= 80 else "B" if score_val >= 60 else "C")

    return {
        # Exact Section 10 fields
        "companyName": lead.get("name") or "",
        "niche": lead.get("niche") or "",
        "city": lead.get("city") or "",
        "country": lead.get("country") or "Brasil",
        "website": lead.get("website_url") or "",
        "instagram": ig_formatted,
        "phone": lead.get("phone") or lead.get("phone_normalized") or "",
        "whatsapp": lead.get("whatsapp") or "",
        "email": lead.get("email") or "",
        "reviews": reviews_summary,
        "score": score_val,
        "priority": priority_val,
        "diagnosis": lead.get("diagnosis") or "",
        "opportunity": lead.get("opportunity_text") or "",
        "source": lead.get("source") or "brag_lead_hunter",
        "discoveredAt": lead.get("discovered_at") or now_iso(),
        # Direct compatibility keys for BRAGHIN_IA (/api/v1/crm/companies/ingest)
        "slug": lead.get("slug") or "empresa",
        "name": lead.get("name") or "",
        "region": f"{lead.get('city') or ''} - {lead.get('state') or ''}".strip(" -") or "Brasil",
        "websiteOriginal": lead.get("website_url") or undefined_if_empty(""),
        "icpScore": score_val,
        "icpTier": f"Prioridade {priority_val}",
        "icpJustification": lead.get("diagnosis") or "",
        "digitalGap": lead.get("opportunity_text") or "",
        "commercialStatus": lead.get("commercial_status") or ("em_analise" if score_val >= 80 else "icp_identificado"),
        "whatsappVerified": bool(lead.get("whatsapp_verified")),
        "pitchWhatsappText": lead.get("commercial_pitch") or "",
        "enrichmentData": {
            "audit_status": lead.get("audit_status"),
            "audit_issues": lead.get("audit_issues"),
            "recommended_offer": lead.get("recommended_offer"),
            "recommended_next_action": lead.get("recommended_next_action"),
            "icp_fit_status": lead.get("icp_fit_status"),
            "data_quality_level": lead.get("data_quality_level"),
            "need_evidence_level": lead.get("need_evidence_level"),
        },
    }


def undefined_if_empty(val: str) -> Optional[str]:
    return val if val else None


def export_leads_to_csv(
    conn: sqlite3.Connection,
    filters: dict[str, Any],
) -> tuple[str, int]:
    leads = query_enriched_leads(
        conn,
        min_score=filters.get("min_score"),
        priority=filters.get("priority"),
        niche=filters.get("niche"),
        city=filters.get("city"),
        has_website=filters.get("has_website"),
        has_instagram=filters.get("has_instagram"),
        search=filters.get("search"),
        limit=int(filters.get("limit") or 1000),
    )

    output = io.StringIO()
    fieldnames = [
        "id", "name", "niche", "subniche", "city", "state", "country",
        "score", "priority", "has_own_website", "website_url", "audit_status",
        "instagram_username", "phone", "whatsapp", "email",
        "google_rating", "google_reviews_count", "followers_count",
        "icp_fit_status", "need_evidence_level", "diagnosis",
        "opportunity_text", "recommended_offer", "recommended_next_action",
        "source", "discovered_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for l in leads:
        row_copy = dict(l)
        row_copy["diagnosis"] = (row_copy.get("diagnosis") or "").replace("\n", " | ")
        writer.writerow(row_copy)

    conn.execute(
        """
        INSERT INTO EXPORT_HISTORY (id, export_type, destination, filters_json, records_count, status, details, exported_at)
        VALUES (?, 'CSV', 'local_download', ?, ?, 'success', 'Exportação CSV concluída', ?)
        """,
        (new_id("exp_h"), json.dumps(filters, ensure_ascii=False), len(leads), now_iso()),
    )
    conn.commit()
    return output.getvalue(), len(leads)


def export_leads_to_json(
    conn: sqlite3.Connection,
    filters: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    leads = query_enriched_leads(
        conn,
        min_score=filters.get("min_score"),
        priority=filters.get("priority"),
        niche=filters.get("niche"),
        city=filters.get("city"),
        has_website=filters.get("has_website"),
        has_instagram=filters.get("has_instagram"),
        search=filters.get("search"),
        limit=int(filters.get("limit") or 1000),
    )
    crm_formatted = [build_brag_crm_payload(l) for l in leads]

    conn.execute(
        """
        INSERT INTO EXPORT_HISTORY (id, export_type, destination, filters_json, records_count, status, details, exported_at)
        VALUES (?, 'JSON', 'local_download', ?, ?, 'success', 'Exportação JSON CRM concluída', ?)
        """,
        (new_id("exp_h"), json.dumps(filters, ensure_ascii=False), len(crm_formatted), now_iso()),
    )
    conn.commit()
    return crm_formatted, len(crm_formatted)


def sync_leads_to_brag_crm(
    conn: sqlite3.Connection,
    company_ids: Optional[list[str]] = None,
    filters: Optional[dict[str, Any]] = None,
    crm_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    Sends selected or filtered leads to the BRAG CRM REST API endpoint (`/api/v1/crm/companies/ingest`).
    Handles offline CRM gracefully by recording the prepared payload and status in EXPORT_HISTORY.
    """
    cfg = get_config()
    base_url = (crm_url or cfg.get("brag_crm_api_url") or "http://localhost:3000").rstrip("/")
    endpoint = f"{base_url}/api/v1/crm/companies/ingest"

    filters = filters or {}
    all_leads = query_enriched_leads(
        conn,
        min_score=filters.get("min_score"),
        priority=filters.get("priority"),
        niche=filters.get("niche"),
        city=filters.get("city"),
        limit=500,
    )
    if company_ids:
        id_set = set(company_ids)
        target_leads = [l for l in all_leads if l["id"] in id_set]
    else:
        target_leads = all_leads

    synced = 0
    failed = 0
    errors: list[dict[str, str]] = []
    payloads_prepared: list[dict[str, Any]] = []

    for lead in target_leads:
        payload = build_brag_crm_payload(lead)
        # Remove None values for clean Zod validation on BRAG CRM
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        payloads_prepared.append(clean_payload)

        headers = {
            "Content-Type": "application/json",
            "x-idempotency-key": f"brag-hunter-{lead['id']}-{lead.get('updated_at') or 'v1'}",
        }
        if cfg.get("brag_crm_api_key"):
            headers["Authorization"] = f"Bearer {cfg['brag_crm_api_key']}"

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(clean_payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if 200 <= resp.status < 300:
                    synced += 1
                else:
                    failed += 1
                    errors.append({"company": lead["name"], "error": f"HTTP {resp.status}"})
        except Exception as e:
            failed += 1
            errors.append({"company": lead["name"], "error": str(e)})

    status_str = "success" if (synced > 0 and failed == 0) else ("partial" if synced > 0 else "prepared_offline")
    details_msg = (
        f"Sincronizados: {synced}/{len(target_leads)} com {endpoint}"
        if synced > 0
        else f"Payloads REST preparados ({len(target_leads)} leads). Servidor CRM destino ({endpoint}) offline no momento."
    )

    conn.execute(
        """
        INSERT INTO EXPORT_HISTORY (id, export_type, destination, filters_json, records_count, status, details, exported_at)
        VALUES (?, 'CRM_REST_API', ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("exp_h"),
            endpoint,
            json.dumps(filters, ensure_ascii=False),
            len(target_leads),
            status_str,
            details_msg,
            now_iso(),
        ),
    )
    conn.commit()

    return {
        "endpoint": endpoint,
        "total_targeted": len(target_leads),
        "synced_live": synced,
        "failed_or_offline": failed,
        "status": status_str,
        "message": details_msg,
        "errors": errors[:5],
        "sample_payload": payloads_prepared[0] if payloads_prepared else None,
    }
