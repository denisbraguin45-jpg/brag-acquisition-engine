"""
BRAG Lead Hunter — Local HTTP API & Static UI Server (`server.py`).
Runs on standard library `http.server.ThreadingHTTPServer` (zero external dependencies).

Provides:
- Static frontend serving (`/` -> `frontend/index.html`)
- `GET /api/dashboard` — Dashboard KPIs, top opportunities, recent campaigns
- `GET /api/leads` — Filtered leads list with full scores, contacts, social, websites, and audits
- `GET /api/companies/<id>` — Full company detail (profile, history, website audit, ICP score breakdown, Agent 14 offer)
- `PATCH /api/companies/<id>/status` — Update commercial status
- `POST /api/companies/<id>/audit` — Trigger live HTTP website audit & rescore for a company
- `GET /api/campaigns` — List campaigns and search history
- `POST /api/campaigns` — Create and launch a new prospecting campaign (async or sync)
- `POST /api/campaigns/<id>/control` — Pause, resume, or stop a campaign
- `GET /api/export/csv` — Download filtered leads as CSV
- `GET /api/export/json` — Download filtered leads as CRM JSON
- `POST /api/export/crm` — Sync leads to BRAG CRM REST API
- `GET /api/export/history` — View export history
- `GET /api/intelligence/agents` — Run Agents 13, 14, 15, and 16 (Market & Sales Intelligence)
- `POST /api/intelligence/experiments` — Create or update a sales experiment (Agent 16)
"""
import json
import sys
import threading
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from backend.agents.workforce import (
    run_agent_13_icp_market_intelligence,
    run_agent_14_offer_intelligence,
    run_agent_15_market_size_intelligence,
    run_agent_16_sales_experiment_intelligence,
    upsert_sales_experiment,
)
from backend.campaign_runner import (
    CAMPAIGN_REGISTRY,
    bootstrap_initial_real_campaign_if_empty,
    create_campaign_record,
    execute_campaign,
)
from backend.config import BASE_DIR, get_config
from backend.sales_distribution import perform_distribution
from backend.sales_service import (
    get_lead_interactions,
    get_sales_leads,
    get_sales_stats,
    record_interaction,
    SCRIPTS_MAP,
)
from backend.connectors.web_enrichment import enrich_from_website_html, fetch_url_html
from backend.connectors.website_auditor import audit_live_website, save_website_audit
from backend.database import get_connection, init_db, now_iso, row_to_dict, rows_to_list
from backend.deduplication import upsert_company_bundle
from backend.exporter import (
    export_leads_to_csv,
    export_leads_to_json,
    query_enriched_leads,
    sync_leads_to_brag_crm,
)
from backend.demo_builder import DEMOS_DIR, generate_top_30_demos
from backend.intelligence.scorer import score_and_save_company

FRONTEND_DIR = BASE_DIR / "frontend"


def get_dashboard_summary(conn) -> dict[str, Any]:
    kpi_row = conn.execute(
        """
        SELECT
            COUNT(c.id) AS companies_found,
            SUM(CASE WHEN COALESCE(s.total_score, 0) >= 60 THEN 1 ELSE 0 END) AS companies_qualified,
            SUM(CASE WHEN s.priority_class = 'A' THEN 1 ELSE 0 END) AS priority_a_leads,
            SUM(CASE WHEN s.priority_class = 'B' THEN 1 ELSE 0 END) AS priority_b_leads,
            SUM(CASE WHEN s.priority_class = 'C' THEN 1 ELSE 0 END) AS priority_c_leads,
            SUM(CASE WHEN s.priority_class = 'D' THEN 1 ELSE 0 END) AS priority_d_leads,
            SUM(CASE WHEN c.has_own_website = 0 THEN 1 ELSE 0 END) AS companies_without_website,
            SUM(CASE WHEN COALESCE(ct.whatsapp, ct.phone_normalized, ct.email, '') != '' THEN 1 ELSE 0 END) AS contacts_found,
            ROUND(AVG(COALESCE(s.total_score, 0)), 1) AS avg_score
        FROM COMPANIES c
        LEFT JOIN ICP_SCORES s ON s.company_id = c.id
        LEFT JOIN CONTACTS ct ON ct.company_id = c.id
        """
    ).fetchone()
    kpis = row_to_dict(kpi_row) or {}
    camp_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM CAMPAIGNS").fetchone()["cnt"]
    kpis["campaigns_executed"] = camp_cnt

    all_top = query_enriched_leads(conn, min_score=60, limit=300)
    ready_100 = [l for l in all_top if l.get("whatsapp") or l.get("phone") or l.get("email")][:105]
    top_opportunities = ready_100 if ready_100 else all_top[:100]
    recent_campaigns = rows_to_list(
        conn.execute("SELECT * FROM CAMPAIGNS ORDER BY updated_at DESC LIMIT 6").fetchall()
    )
    for c in recent_campaigns:
        for jcol in ("config_json", "errors_log", "progress_log"):
            try:
                c[jcol] = json.loads(c.get(jcol) or ("{}" if jcol == "config_json" else "[]"))
            except Exception:
                c[jcol] = {} if jcol == "config_json" else []

    niche_dist = rows_to_list(
        conn.execute(
            """
            SELECT c.niche, COUNT(*) AS total,
                   SUM(CASE WHEN c.has_own_website = 0 THEN 1 ELSE 0 END) AS no_site,
                   SUM(CASE WHEN s.priority_class = 'A' THEN 1 ELSE 0 END) AS class_a
            FROM COMPANIES c
            LEFT JOIN ICP_SCORES s ON s.company_id = c.id
            GROUP BY c.niche
            ORDER BY total DESC
            """
        ).fetchall()
    )

    return {
        "kpis": kpis,
        "top_opportunities": top_opportunities,
        "recent_campaigns": recent_campaigns,
        "niche_distribution": niche_dist,
    }


def get_company_full_detail(conn, company_id: str) -> Optional[dict[str, Any]]:
    comp_row = conn.execute("SELECT * FROM COMPANIES WHERE id = ? OR slug = ? LIMIT 1", (company_id, company_id)).fetchone()
    if not comp_row:
        return None
    comp = row_to_dict(comp_row) or {}
    cid = comp["id"]

    for jcol in ("services_offered", "history_log"):
        try:
            comp[jcol] = json.loads(comp.get(jcol) or "[]")
        except Exception:
            comp[jcol] = []

    contacts = rows_to_list(conn.execute("SELECT * FROM CONTACTS WHERE company_id = ?", (cid,)).fetchall())
    socials = rows_to_list(conn.execute("SELECT * FROM SOCIAL_PROFILES WHERE company_id = ?", (cid,)).fetchall())
    websites = rows_to_list(conn.execute("SELECT * FROM WEBSITES WHERE company_id = ?", (cid,)).fetchall())
    audits = rows_to_list(conn.execute("SELECT * FROM AUDITS WHERE company_id = ?", (cid,)).fetchall())
    for a in audits:
        for jcol in ("issues_found", "improvement_opportunities"):
            try:
                a[jcol] = json.loads(a.get(jcol) or "[]")
            except Exception:
                a[jcol] = []

    score_row = conn.execute("SELECT * FROM ICP_SCORES WHERE company_id = ? LIMIT 1", (cid,)).fetchone()
    score_dict = row_to_dict(score_row) or {}
    if score_dict:
        try:
            score_dict["justifications"] = json.loads(score_dict.get("justifications") or "[]")
        except Exception:
            score_dict["justifications"] = []

    offer_intel = run_agent_14_offer_intelligence(conn, company_id=cid)

    return {
        "company": comp,
        "contacts": contacts,
        "social_profiles": socials,
        "websites": websites,
        "audits": audits,
        "icp_score": score_dict,
        "offer_intelligence": offer_intel.get("company_specific_recommendation"),
    }


class BragLeadHunterHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Quiet clean logging
        pass

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, content_type: str, body: bytes, filename: Optional[str] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="ignore")
        return json.loads(raw) if raw.strip() else {}

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        q_first = lambda k, default=None: qs.get(k, [default])[0]

        try:
            if path in ("/", "/index.html"):
                html_path = FRONTEND_DIR / "index.html"
                if html_path.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", html_path.read_bytes())
                else:
                    self._send_json(404, {"error": "Frontend index.html not found"})
                return

            if path == "/demos" or path == "/demos/":
                hub_file = DEMOS_DIR / "index.html"
                if not hub_file.exists():
                    generate_top_30_demos()
                if hub_file.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", hub_file.read_bytes())
                else:
                    self._send_json(404, {"error": "Hub index não encontrado"})
                return

            if path == "/demos/manifest.json":
                m_file = DEMOS_DIR / "manifest.json"
                if not m_file.exists():
                    generate_top_30_demos()
                if m_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", m_file.read_bytes())
                else:
                    self._send_json(404, {"error": "Manifest não encontrado"})
                return

            if path == "/demos/sales.html":
                s_file = DEMOS_DIR / "sales.html"
                if s_file.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", s_file.read_bytes())
                else:
                    self._send_json(404, {"error": "sales.html não encontrado"})
                return

            if path == "/demos/sales_distribution_400.json":
                sd_file = DEMOS_DIR / "sales_distribution_400.json"
                if sd_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", sd_file.read_bytes())
                else:
                    self._send_json(404, {"error": "sales_distribution_400.json não encontrado"})
                return

            if path == "/demos/crm.html":
                crm_file = DEMOS_DIR / "crm.html"
                if crm_file.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", crm_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm.html não encontrado"})
                return

            if path == "/demos/crm_all_leads.json":
                j_file = DEMOS_DIR / "crm_all_leads.json"
                if j_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", j_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm_all_leads.json não encontrado"})
                return

            if path == "/demos/database_all_demos.json":
                db_file = DEMOS_DIR / "database_all_demos.json"
                if db_file.exists():
                    self._send_bytes(200, "application/json; charset=utf-8", db_file.read_bytes())
                else:
                    self._send_json(404, {"error": "database_all_demos.json não encontrado"})
                return

            if path == "/demos/crm_all_leads.csv":
                c_file = DEMOS_DIR / "crm_all_leads.csv"
                if c_file.exists():
                    self._send_bytes(200, "text/csv; charset=utf-8", c_file.read_bytes())
                else:
                    self._send_json(404, {"error": "crm_all_leads.csv não encontrado"})
                return

            if path.startswith("/demos/"):
                rel_parts = [p for p in path.split("/demos/")[1].split("/") if p and p != ".."]
                if not rel_parts:
                    self._send_json(404, {"error": "Demo não especificada"})
                    return
                slug_part = rel_parts[0]
                if len(rel_parts) >= 3 and rel_parts[1] == "images":
                    img_file = DEMOS_DIR / slug_part / "images" / rel_parts[2]
                    if img_file.exists() and img_file.is_file():
                        ext = img_file.suffix.lower()
                        ctype = "image/png" if ext == ".png" else ("image/webp" if ext == ".webp" else "image/jpeg")
                        self._send_bytes(200, ctype, img_file.read_bytes())
                        return
                    self._send_json(404, {"error": "Imagem da demo não encontrada"})
                    return

                demo_file = DEMOS_DIR / slug_part / "index.html"
                if not demo_file.exists():
                    generate_top_30_demos()
                if demo_file.exists():
                    self._send_bytes(200, "text/html; charset=utf-8", demo_file.read_bytes())
                else:
                    self._send_json(404, {"error": f"Demo '{slug_part}' não encontrada"})
                return

            if path == "/api/health":
                cfg = get_config()
                self._send_json(200, {
                    "ok": True,
                    "service": "BRAG Lead Hunter — Local Prospecting Engine",
                    "has_apify_token": bool(cfg.get("apify_token")),
                    "has_google_places_key": bool(cfg.get("google_places_api_key")),
                    "crm_url": cfg.get("brag_crm_api_url"),
                })
                return

            conn = get_connection()
            try:
                if path == "/api/dashboard":
                    self._send_json(200, get_dashboard_summary(conn))
                    return

                if path == "/api/demos":
                    manifest_file = DEMOS_DIR / "manifest.json"
                    if not manifest_file.exists():
                        items = generate_top_30_demos(conn)
                    else:
                        items = json.loads(manifest_file.read_text(encoding="utf-8"))
                        # Sync live commercial_status from DB
                        status_rows = conn.execute("SELECT id, commercial_status FROM COMPANIES").fetchall()
                        status_map = {r["id"]: r["commercial_status"] for r in status_rows}
                        for item in items:
                            if item.get("company_id") in status_map:
                                item["commercial_status"] = status_map[item["company_id"]]
                    self._send_json(200, {"total": len(items), "items": items})
                    return

                if path == "/api/leads":
                    min_score_raw = q_first("min_score")
                    leads = query_enriched_leads(
                        conn,
                        min_score=int(min_score_raw) if min_score_raw and min_score_raw.isdigit() else None,
                        priority=q_first("priority"),
                        niche=q_first("niche"),
                        city=q_first("city"),
                        has_website=q_first("has_website"),
                        has_instagram=q_first("has_instagram"),
                        search=q_first("search"),
                        limit=int(q_first("limit", "500")),
                    )
                    self._send_json(200, {"total": len(leads), "items": leads})
                    return

                if path.startswith("/api/companies/"):
                    comp_id = path.split("/api/companies/")[1].split("/")[0]
                    detail = get_company_full_detail(conn, comp_id)
                    if not detail:
                        self._send_json(404, {"error": "Empresa não encontrada"})
                    else:
                        self._send_json(200, detail)
                    return

                if path == "/api/campaigns":
                    camps = rows_to_list(conn.execute("SELECT * FROM CAMPAIGNS ORDER BY created_at DESC LIMIT 30").fetchall())
                    for c in camps:
                        for jcol in ("config_json", "errors_log", "progress_log"):
                            try:
                                c[jcol] = json.loads(c.get(jcol) or ("{}" if jcol == "config_json" else "[]"))
                            except Exception:
                                c[jcol] = {} if jcol == "config_json" else []
                    history = rows_to_list(conn.execute("SELECT * FROM SEARCH_HISTORY ORDER BY executed_at DESC LIMIT 40").fetchall())
                    self._send_json(200, {"campaigns": camps, "search_history": history})
                    return

                if path == "/api/export/csv":
                    filters = {
                        "min_score": int(q_first("min_score")) if q_first("min_score") and str(q_first("min_score")).isdigit() else None,
                        "priority": q_first("priority"),
                        "niche": q_first("niche"),
                        "city": q_first("city"),
                        "has_website": q_first("has_website"),
                    }
                    csv_text, _ = export_leads_to_csv(conn, filters)
                    self._send_bytes(
                        200,
                        "text/csv; charset=utf-8",
                        ("\ufeff" + csv_text).encode("utf-8"),
                        filename="brag_leads_export.csv",
                    )
                    return

                if path == "/api/export/json":
                    filters = {
                        "min_score": int(q_first("min_score")) if q_first("min_score") and str(q_first("min_score")).isdigit() else None,
                        "priority": q_first("priority"),
                        "niche": q_first("niche"),
                        "city": q_first("city"),
                        "has_website": q_first("has_website"),
                    }
                    json_list, _ = export_leads_to_json(conn, filters)
                    body = json.dumps(json_list, ensure_ascii=False, indent=2).encode("utf-8")
                    self._send_bytes(
                        200,
                        "application/json; charset=utf-8",
                        body,
                        filename="brag_leads_crm_export.json",
                    )
                    return

                if path == "/api/export/history":
                    rows = rows_to_list(conn.execute("SELECT * FROM EXPORT_HISTORY ORDER BY exported_at DESC LIMIT 30").fetchall())
                    self._send_json(200, {"items": rows})
                    return

                if path == "/api/intelligence/agents":
                    a13 = run_agent_13_icp_market_intelligence(conn)
                    a14 = run_agent_14_offer_intelligence(conn)
                    a15 = run_agent_15_market_size_intelligence(conn)
                    a16 = run_agent_16_sales_experiment_intelligence(conn)
                    self._send_json(200, {
                        "agent_13_icp_market": a13,
                        "agent_14_offer_intelligence": a14,
                        "agent_15_market_size": a15,
                        "agent_16_sales_experiments": a16,
                    })
                    return

                # --- Sales Operation Module (Bruce & Gabriel 400 Leads) ---
                if path == "/api/sales/stats":
                    self._send_json(200, get_sales_stats())
                    return

                if path == "/api/sales/leads":
                    vendor_q = q_first("vendor")
                    class_q = q_first("classification")
                    priority_q = q_first("priority")
                    leads = get_sales_leads(vendor=vendor_q, classification=class_q, priority=priority_q)
                    self._send_json(200, {"total": len(leads), "items": leads})
                    return

                if path.startswith("/api/sales/leads/") and path.endswith("/interactions"):
                    slug = path.split("/api/sales/leads/")[1].split("/")[0]
                    logs = get_lead_interactions(slug)
                    self._send_json(200, {"slug": slug, "interactions": logs})
                    return

                if path == "/api/sales/scripts":
                    self._send_json(200, {"scripts": SCRIPTS_MAP})
                    return

                self._send_json(404, {"error": f"Rota {path} não encontrada"})
            finally:
                conn.close()
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json_body()
            conn = get_connection()
            try:
                if path == "/api/campaigns":
                    camp = create_campaign_record(conn, body)
                    run_sync = bool(body.get("run_sync", False))
                    live_audit = bool(body.get("perform_live_http_audit", True))
                    if run_sync:
                        final_camp = execute_campaign(camp["id"], perform_live_http_audit=live_audit)
                        self._send_json(201, {"campaign": final_camp})
                    else:
                        t = threading.Thread(
                            target=execute_campaign,
                            kwargs={"campaign_id": camp["id"], "perform_live_http_audit": live_audit},
                            daemon=True,
                        )
                        t.start()
                        self._send_json(201, {"campaign": camp, "message": "Campanha iniciada em segundo plano."})
                    return

                if path.startswith("/api/campaigns/") and path.endswith("/control"):
                    camp_id = path.split("/api/campaigns/")[1].split("/")[0]
                    action = (body.get("action") or "").lower()
                    if action == "pause":
                        CAMPAIGN_REGISTRY.set_state(camp_id, "paused")
                        conn.execute("UPDATE CAMPAIGNS SET status = 'paused', updated_at = ? WHERE id = ?", (now_iso(), camp_id))
                        conn.commit()
                    elif action == "resume":
                        current_row = conn.execute("SELECT status FROM CAMPAIGNS WHERE id = ?", (camp_id,)).fetchone()
                        CAMPAIGN_REGISTRY.set_state(camp_id, "running")
                        conn.execute("UPDATE CAMPAIGNS SET status = 'running', updated_at = ? WHERE id = ?", (now_iso(), camp_id))
                        conn.commit()
                        if current_row and current_row["status"] in ("paused", "created", "idle"):
                            t = threading.Thread(target=execute_campaign, kwargs={"campaign_id": camp_id}, daemon=True)
                            t.start()
                    elif action == "stop":
                        CAMPAIGN_REGISTRY.set_state(camp_id, "stopped")
                        conn.execute("UPDATE CAMPAIGNS SET status = 'paused', updated_at = ? WHERE id = ?", (now_iso(), camp_id))
                        conn.commit()
                    updated = row_to_dict(conn.execute("SELECT * FROM CAMPAIGNS WHERE id = ?", (camp_id,)).fetchone())
                    self._send_json(200, {"campaign": updated})
                    return

                if path.startswith("/api/companies/") and path.endswith("/audit"):
                    comp_id = path.split("/api/companies/")[1].split("/")[0]
                    comp = row_to_dict(conn.execute("SELECT * FROM COMPANIES WHERE id = ?", (comp_id,)).fetchone())
                    if not comp:
                        self._send_json(404, {"error": "Empresa não encontrada"})
                        return
                    web_row = row_to_dict(conn.execute("SELECT * FROM WEBSITES WHERE company_id = ? LIMIT 1", (comp_id,)).fetchone())
                    url_to_test = body.get("url") or (web_row or {}).get("url") or ""
                    audit_res = audit_live_website(url_to_test, timeout=6.0)
                    save_website_audit(conn, comp_id, audit_res)
                    if audit_res.get("http_available") and url_to_test:
                        ok, _, final_u, html_str = fetch_url_html(url_to_test, timeout=5.0)
                        if ok and html_str:
                            enr = enrich_from_website_html(html_str, final_u, comp.get("niche") or "")
                            upsert_company_bundle(conn, {**comp, "website_url": final_u, "has_own_website": True, **enr})
                    score_and_save_company(conn, comp_id)
                    conn.commit()
                    self._send_json(200, get_company_full_detail(conn, comp_id))
                    return

                if path == "/api/export/crm":
                    res = sync_leads_to_brag_crm(
                        conn,
                        company_ids=body.get("company_ids"),
                        filters=body.get("filters") or {},
                        crm_url=body.get("crm_url"),
                    )
                    self._send_json(200, res)
                    return

                if path == "/api/intelligence/experiments":
                    exp = upsert_sales_experiment(conn, body)
                    self._send_json(200, {"experiment": exp})
                    return

                if path == "/api/demos/regenerate":
                    items = generate_top_30_demos(conn)
                    self._send_json(200, {"ok": True, "total": len(items), "items": items})
                    return

                # --- Sales Operation Module POST Endpoints ---
                if path == "/api/sales/interaction":
                    lead_slug = body.get("slug") or body.get("lead_slug")
                    if not lead_slug:
                        self._send_json(400, {"error": "lead_slug/slug é obrigatório"})
                        return
                    res = record_interaction(
                        lead_slug=lead_slug,
                        vendor=body.get("vendor"),
                        call_outcome=body.get("call_outcome"),
                        stage=body.get("stage"),
                        classification=body.get("classification"),
                        next_action=body.get("next_action"),
                        next_contact_at=body.get("next_contact_at"),
                        notes=body.get("notes"),
                        deal_value=body.get("deal_value"),
                    )
                    self._send_json(200, {"ok": True, "lead": res})
                    return

                if path == "/api/sales/distribute":
                    res = perform_distribution(force=True)
                    self._send_json(200, {"ok": True, "distribution": res})
                    return

                self._send_json(404, {"error": f"Rota POST {path} não encontrada"})
            finally:
                conn.close()
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def do_PATCH(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json_body()
            conn = get_connection()
            try:
                if path.startswith("/api/companies/") and path.endswith("/status"):
                    comp_id = path.split("/api/companies/")[1].split("/")[0]
                    new_status = body.get("commercial_status") or "em_analise"
                    conn.execute(
                        "UPDATE COMPANIES SET commercial_status = ?, updated_at = ? WHERE id = ?",
                        (new_status, now_iso(), comp_id),
                    )
                    conn.commit()
                    self._send_json(200, {"ok": True, "company_id": comp_id, "commercial_status": new_status})
                    return

                self._send_json(404, {"error": f"Rota PATCH {path} não encontrada"})
            finally:
                conn.close()
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def run_server(port: Optional[int] = None, open_browser: bool = False) -> None:
    cfg = get_config()
    listen_port = port or cfg["port"]
    init_db()
    bootstrap_initial_real_campaign_if_empty()
    if not (DEMOS_DIR / "manifest.json").exists():
        generate_top_30_demos()

    ThreadingHTTPServer.allow_reuse_address = True
    try:
        server = ThreadingHTTPServer(("0.0.0.0", listen_port), BragLeadHunterHandler)
    except OSError:
        print(f"\n[AVISO] O servidor BRAG Lead Hunter já está em execução na porta {listen_port}!")
        print(f"👉 Acesse no navegador: http://localhost:{listen_port}\n")
        if open_browser:
            webbrowser.open(f"http://localhost:{listen_port}")
        return

    print(f"\n============================================================")
    print(f"  BRAG LEAD HUNTER — LOCAL PROSPECTING ENGINE")
    print(f"  Status: ONLINE E PRONTO PARA USO")
    print(f"  Abra no navegador: http://localhost:{listen_port}")
    print(f"  Banco SQLite: {cfg['db_path']}")
    print(f"  (Pressione Ctrl+C para encerrar)")
    print(f"============================================================\n", flush=True)
    if open_browser:
        webbrowser.open(f"http://localhost:{listen_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor BRAG Lead Hunter...")
        server.server_close()


if __name__ == "__main__":
    run_server(open_browser=("--open" in sys.argv))
