"""
Executes a real validation campaign on accessible public data:
1. Initializes SQLite database (`data/brag_lead_hunter.db`).
2. Runs multi-city, multi-niche campaign combining:
   - Connector B (Instagram Comercial — real Antigravity dataset + contact extraction)
   - Connector A (Google Maps / OpenStreetMap Overpass public establishments)
   - Connector C (Web Enrichment)
   - Connector D (Website Auditor with live HTTP checks on discovered websites)
3. Runs Agents 13, 14, 15, and 16.
4. Exports CSV and JSON files into `data/` and prints a comprehensive verification report.
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.agents.workforce import (
    run_agent_13_icp_market_intelligence,
    run_agent_14_offer_intelligence,
    run_agent_15_market_size_intelligence,
    run_agent_16_sales_experiment_intelligence,
)
from backend.campaign_runner import create_campaign_record, execute_campaign
from backend.config import DATA_DIR, get_config
from backend.connectors.website_auditor import audit_live_website, save_website_audit
from backend.database import get_connection, init_db
from backend.exporter import export_leads_to_csv, export_leads_to_json, query_enriched_leads
from backend.intelligence.scorer import score_and_save_company


def main() -> None:
    cfg = get_config()
    init_db(cfg["db_path"])
    conn = get_connection(cfg["db_path"])

    try:
        camp = create_campaign_record(
            conn,
            {
                "name": "Campanha Real de Validação — 100+ Contatos Prontos (Multimarcas, Supercarros, Blindados & Náutica)",
                "country": "Brasil",
                "state": "SP",
                "cities": ["Todas"],
                "niches": [""],
                "desired_quantity": 250,
                "website_filter": "all",
                "instagram_filter": "all",
                "min_icp_score": 60,
                "sources": ["instagram", "web_enrichment", "website_auditor"],
            },
        )
    finally:
        conn.close()

    # Execute campaign
    result_camp = execute_campaign(camp["id"], db_path=cfg["db_path"], perform_live_http_audit=False)

    # Also perform live HTTP Website Audits on up to 6 companies that have an own website URL
    conn = get_connection(cfg["db_path"])
    try:
        with_sites = conn.execute(
            """
            SELECT c.id, c.name, w.url
            FROM COMPANIES c
            JOIN WEBSITES w ON w.company_id = c.id
            WHERE c.has_own_website = 1 AND w.url != ''
            LIMIT 6
            """
        ).fetchall()

        live_audited = []
        for row in with_sites:
            aud = audit_live_website(row["url"], timeout=5.0)
            save_website_audit(conn, row["id"], aud)
            sc = score_and_save_company(conn, row["id"])
            live_audited.append({
                "name": row["name"],
                "url": row["url"],
                "http_status": aud.get("http_status"),
                "load_time_ms": aud.get("load_time_ms"),
                "has_https": aud.get("has_https"),
                "is_responsive": aud.get("is_responsive"),
                "audit_status": aud.get("audit_status"),
                "issues": aud.get("issues_found"),
                "new_score": sc.get("total_score"),
            })
        conn.commit()

        # Generate CSV & JSON exports on disk
        csv_text, csv_count = export_leads_to_csv(conn, {"min_score": 60})
        (DATA_DIR / "brag_leads_qualified.csv").write_text(csv_text, encoding="utf-8")

        json_list, json_count = export_leads_to_json(conn, {"min_score": 60})
        (DATA_DIR / "brag_leads_crm_payloads.json").write_text(
            json.dumps(json_list, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Fetch summary stats
        top_a = query_enriched_leads(conn, priority="A", limit=5)
        a13 = run_agent_13_icp_market_intelligence(conn)
        a15 = run_agent_15_market_size_intelligence(conn)
        a16 = run_agent_16_sales_experiment_intelligence(conn)

        report = {
            "campaign": {
                "id": result_camp["id"],
                "name": result_camp["name"],
                "status": result_camp["status"],
                "total_found": result_camp["total_found"],
                "total_qualified": result_camp["total_qualified"],
                "new_records": result_camp["new_records"],
                "duplicates_avoided": result_camp["duplicates_avoided"],
            },
            "live_website_audits_sample": live_audited,
            "top_5_priority_a_leads": [
                {
                    "name": l["name"],
                    "niche": l["niche"],
                    "city": f"{l['city']}-{l['state']}",
                    "score": l["score"],
                    "priority": l["priority"],
                    "instagram": f"@{l['instagram_username']}" if l.get("instagram_username") else "",
                    "whatsapp_or_phone": l.get("whatsapp") or l.get("phone") or "",
                    "has_own_website": bool(l.get("has_own_website")),
                    "link_type": l.get("link_type"),
                    "opportunity": l.get("opportunity_text"),
                }
                for l in top_a
            ],
            "exports_generated": {
                "csv_file": str(DATA_DIR / "brag_leads_qualified.csv"),
                "csv_records": csv_count,
                "json_file": str(DATA_DIR / "brag_leads_crm_payloads.json"),
                "json_records": json_count,
            },
            "agent_15_funnel": a15["local_database_funnel_distinction"],
            "agent_16_verdict": a16["executive_verdict"],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
