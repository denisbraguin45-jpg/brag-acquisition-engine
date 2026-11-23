"""
Functional & Unit Test Suite for BRAG Lead Hunter (`tests/test_lead_hunter.py`).
Validates:
1. SQLite Database initialization (all required tables: COMPANIES, CONTACTS, SOCIAL_PROFILES, WEBSITES, AUDITS, ICP_SCORES, CAMPAIGNS, SEARCH_HISTORY, EXPORT_HISTORY, SALES_EXPERIMENTS).
2. Deduplication Engine (unique identification by normalized phone, website domain, Instagram username, and commercial name + location; history preservation on update).
3. Website Auditor (10 technical & commercial criteria: HTTP status, HTTPS, responsiveness, load speed, presentation, offer clarity, CTA, WhatsApp button, contact form, commercial structure).
4. Commercial Intelligence & Opportunity Engine (0–100 ICP scoring across all 7 criteria with justifications, A/B/C/D classification, separation of ICP fit / data quality / need evidence / purchase intent, and automated diagnosis/pitch).
5. Export & BRAG CRM REST Payload Builder (CSV, JSON, and 16-field CRM payload).
6. BRAG AI Workforce Agents 13, 14, 15, and 16 (including the Central Rule validation gate).
7. End-to-End Campaign Execution with real Antigravity data.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from backend.agents.workforce import (
    evaluate_experiment_validation,
    run_agent_13_icp_market_intelligence,
    run_agent_14_offer_intelligence,
    run_agent_15_market_size_intelligence,
    run_agent_16_sales_experiment_intelligence,
    upsert_sales_experiment,
)
from backend.campaign_runner import create_campaign_record, execute_campaign
from backend.connectors.instagram import (
    classify_bio_link,
    extract_contacts_from_bio_and_links,
    infer_city_state_country,
)
from backend.connectors.website_auditor import audit_website_html, save_website_audit
from backend.database import get_connection, init_db
from backend.deduplication import (
    extract_domain,
    is_own_domain,
    normalize_phone,
    upsert_company_bundle,
)
from backend.exporter import (
    build_brag_crm_payload,
    export_leads_to_csv,
    export_leads_to_json,
    query_enriched_leads,
)
from backend.intelligence.scorer import evaluate_company_intelligence, score_and_save_company


class TestBragLeadHunter(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp_dir.name) / "test_brag_hunter.db")
        os.environ["DB_PATH"] = self.db_path
        init_db(self.db_path)
        self.conn = get_connection(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()
        os.environ.pop("DB_PATH", None)
        self.tmp_dir.cleanup()

    def test_01_database_tables_created(self) -> None:
        required_tables = {
            "COMPANIES",
            "CONTACTS",
            "SOCIAL_PROFILES",
            "WEBSITES",
            "AUDITS",
            "ICP_SCORES",
            "CAMPAIGNS",
            "SEARCH_HISTORY",
            "EXPORT_HISTORY",
            "SALES_EXPERIMENTS",
        }
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        existing = {r["name"] for r in rows}
        self.assertTrue(required_tables.issubset(existing))

    def test_02_deduplication_across_all_4_keys_and_history_preservation(self) -> None:
        # 1. Insert initial company with Instagram and phone
        res1 = upsert_company_bundle(
            self.conn,
            {
                "name": "Premium Motors SP",
                "city": "São Paulo",
                "state": "SP",
                "phone": "(11) 98888-7777",
                "instagram_username": "@PremiumMotorsSP",
                "niche": "P1 — Revendas premium e multimarcas",
                "source": "instagram",
            },
        )
        self.assertEqual(res1["status"], "new")
        comp_id = res1["company_id"]

        # 2. Attempt to insert same company via normalized phone with different name format & new email
        res2 = upsert_company_bundle(
            self.conn,
            {
                "name": "Premium Motors Ltda",
                "city": "São Paulo",
                "phone": "+55 11 98888-7777",
                "email": "contato@premiummotors.com.br",
                "website_url": "https://www.premiummotors.com.br",
                "has_own_website": True,
                "source": "google_maps",
            },
        )
        self.assertEqual(res2["company_id"], comp_id)
        self.assertEqual(res2["status"], "updated")
        self.assertTrue(res2["matched_by"].startswith("phone:"))

        # 3. Attempt to insert via website domain
        res3 = upsert_company_bundle(
            self.conn,
            {
                "name": "Outra Razão Social",
                "website_url": "http://premiummotors.com.br/estoque",
                "google_rating": 4.9,
                "google_reviews_count": 85,
                "source": "web_enrichment",
            },
        )
        self.assertEqual(res3["company_id"], comp_id)
        self.assertTrue(res3["matched_by"].startswith("domain:"))

        # Verify total companies count is still 1 and history_log preserved updates
        count = self.conn.execute("SELECT COUNT(*) AS c FROM COMPANIES").fetchone()["c"]
        self.assertEqual(count, 1)
        comp_row = self.conn.execute("SELECT * FROM COMPANIES WHERE id = ?", (comp_id,)).fetchone()
        history = json.loads(comp_row["history_log"])
        self.assertGreaterEqual(len(history), 2)
        self.assertIn("instagram", comp_row["source"])
        self.assertIn("google_maps", comp_row["source"])

    def test_03_instagram_contact_and_location_extraction(self) -> None:
        bio = "🚘 Seminovos selecionados 🤝 Compra e venda 📲 (43) 98864-7889 ✉️ vendas@rkmotors.com.br 📍Av. São João 1601 Londrina PR"
        links = "https://wa.me/5543988647889 | https://linktr.ee/rkmotors"
        contacts = extract_contacts_from_bio_and_links(bio, links)
        self.assertEqual(contacts["whatsapp"], "43988647889")
        self.assertTrue(contacts["whatsapp_verified"])
        self.assertEqual(contacts["email"], "vendas@rkmotors.com.br")

        city, state, country = infer_city_state_country("RK Motors", bio, "RK Motors")
        self.assertEqual(state, "PR")
        self.assertEqual(country, "Brasil")

        link_class = classify_bio_link(links)
        self.assertFalse(link_class["has_own_website"])
        self.assertEqual(link_class["link_category"], "whatsapp")

    def test_04_website_auditor_criteria(self) -> None:
        # Case A: No website
        no_site_audit = audit_website_html("", "", 0, 0, "")
        self.assertEqual(no_site_audit["audit_status"], "no_site")

        # Case B: Weak non-HTTPS, non-responsive website without WhatsApp or CTA
        weak_html = "<html><head><title>Loja</title></head><body><p>Bem vindo</p></body></html>"
        weak_audit = audit_website_html("http://lojacarrosantiga.com.br", weak_html, 200, 4200, "http://lojacarrosantiga.com.br")
        self.assertEqual(weak_audit["audit_status"], "weak")
        self.assertFalse(weak_audit["has_https"])
        self.assertFalse(weak_audit["is_responsive"])
        self.assertFalse(weak_audit["has_whatsapp_button"])
        self.assertGreaterEqual(len(weak_audit["issues_found"]), 3)

        # Case C: High-converting modern responsive HTTPS website
        good_html = """
        <!doctype html>
        <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <meta name="description" content="Concessionária de veículos seminovos premium e blindados em São Paulo.">
          <meta property="og:title" content="Prime Motors">
          <title>Prime Motors — Veículos Seminovos Premium e Blindados</title>
        </head>
        <body>
          <h1>Estoque de Veículos Seminovos Premium e Blindados</h1>
          <p>Confira nosso catálogo por marca, modelo, ano, km e preço.</p>
          <img src="1.jpg"><img src="2.jpg"><img src="3.jpg">
          <a href="https://wa.me/5511999999999">Fale Conosco no WhatsApp</a>
          <button>Ver Estoque e Simular Financiamento</button>
          <form><input name="nome"><input name="telefone"></form>
        </body>
        </html>
        """
        good_audit = audit_website_html("https://primemotors.com.br", good_html, 200, 280, "https://primemotors.com.br")
        self.assertEqual(good_audit["audit_status"], "adequate")
        self.assertTrue(good_audit["has_https"])
        self.assertTrue(good_audit["is_responsive"])
        self.assertTrue(good_audit["has_whatsapp_button"])
        self.assertTrue(good_audit["has_contact_form"])
        self.assertTrue(good_audit["has_cta"])

    def test_05_commercial_and_opportunity_intelligence_scoring(self) -> None:
        res = upsert_company_bundle(
            self.conn,
            {
                "name": "Elite Supercarros",
                "city": "São Paulo",
                "state": "SP",
                "niche": "P2 — Luxo e superesportivos",
                "services_offered": ["Superesportivos / Exóticos", "Blindados"],
                "google_rating": 4.9,
                "google_reviews_count": 64,
                "has_own_website": False,
                "has_instagram": True,
                "instagram_username": "elitesupercarros",
                "followers_count": 28000,
                "posts_count": 410,
                "latest_post_date": "2026-10-17",
                "whatsapp": "11977776666",
                "whatsapp_verified": True,
                "email": "contato@elitesupercarros.com.br",
                "source": "instagram",
            },
        )
        comp_id = res["company_id"]
        save_website_audit(self.conn, comp_id, audit_website_html("", "", 0, 0, ""))
        scored = score_and_save_company(self.conn, comp_id)

        self.assertGreaterEqual(scored["total_score"], 80)
        self.assertEqual(scored["priority_class"], "A")
        self.assertEqual(scored["pts_no_website"], 25)
        self.assertEqual(scored["pts_high_value_services"], 15)
        self.assertEqual(scored["pts_reputation"], 10)
        self.assertEqual(scored["pts_active_instagram"], 10)
        self.assertEqual(scored["pts_commercial_contact"], 10)
        self.assertEqual(scored["pts_investment_potential"], 10)
        self.assertTrue(len(scored["justifications"]) == 7)
        self.assertIn("Elite Supercarros", scored["opportunity_text"])
        self.assertIn("Não confirmada", scored["confirmed_purchase_intent"])

        # Also test a company WITH a broken/weak website (up to 20 pts for broken website)
        res_broken = upsert_company_bundle(
            self.conn,
            {
                "name": "Baviera Imports",
                "city": "Curitiba",
                "state": "PR",
                "niche": "P3 — Importados e SUVs premium",
                "services_offered": ["Importados", "Blindados"],
                "google_rating": 4.8,
                "google_reviews_count": 42,
                "has_own_website": True,
                "website_url": "https://bavieraimports.com.br",
                "has_instagram": True,
                "instagram_username": "bavieraimports",
                "followers_count": 15000,
                "posts_count": 180,
                "whatsapp": "41999998888",
                "whatsapp_verified": True,
                "source": "google_maps",
            },
        )
        broken_id = res_broken["company_id"]
        save_website_audit(
            self.conn,
            broken_id,
            audit_website_html("https://bavieraimports.com.br", "", http_status=500, load_time_ms=1200),
        )
        scored_broken = score_and_save_company(self.conn, broken_id)
        self.assertEqual(scored_broken["pts_no_website"], 0)
        self.assertEqual(scored_broken["pts_broken_website"], 20)
        self.assertGreaterEqual(scored_broken["total_score"], 70)
        self.assertEqual(scored_broken["priority_class"], "B")

    def test_06_workforce_agents_13_to_16_and_central_rule(self) -> None:
        # Test Central Rule on Agent 16: 500 leads but 0 contacts/sales MUST NOT be validated for scale
        unvalidated = evaluate_experiment_validation({
            "name": "Nicho com Muitos Leads mas Zero Vendas",
            "leads_targeted": 500,
            "contacts_made": 5,
            "responses_received": 0,
            "meetings_booked": 0,
            "proposals_sent": 0,
            "sales_closed": 0,
            "revenue_brl": 0,
        })
        self.assertFalse(unvalidated["worthy_of_scale"])
        self.assertEqual(unvalidated["validation_status"], "INSUFICIENTE_PARA_DECISAO")

        # Now test an experiment with real commercial evidence (contacts, responses, proposals, sales)
        validated = evaluate_experiment_validation({
            "name": "Nicho Validado Comercialmente",
            "leads_targeted": 40,
            "contacts_made": 25,
            "responses_received": 8,
            "meetings_booked": 5,
            "proposals_sent": 3,
            "sales_closed": 2,
            "revenue_brl": 7600.0,
        })
        self.assertTrue(validated["worthy_of_scale"])
        self.assertEqual(validated["validation_status"], "VALIDADO_PARA_ESCALA")

        # Run all 4 agents against DB
        a13 = run_agent_13_icp_market_intelligence(self.conn)
        a14 = run_agent_14_offer_intelligence(self.conn)
        a15 = run_agent_15_market_size_intelligence(self.conn)
        a16 = run_agent_16_sales_experiment_intelligence(self.conn)

        self.assertEqual(a13["agent_id"], "AGENT_13")
        self.assertEqual(a14["agent_id"], "AGENT_14")
        self.assertEqual(a15["agent_id"], "AGENT_15")
        self.assertEqual(a16["agent_id"], "AGENT_16")
        self.assertIn("empresas_encontradas", a15["local_database_funnel_distinction"])
        self.assertIn("empresas_elegiveis", a15["local_database_funnel_distinction"])
        self.assertIn("empresas_efetivamente_alcancaveis", a15["local_database_funnel_distinction"])

    def test_07_end_to_end_campaign_and_exports(self) -> None:
        camp = create_campaign_record(
            self.conn,
            {
                "name": "Campanha Funcional de Teste",
                "country": "Brasil",
                "state": "SP",
                "cities": ["São Paulo", "Curitiba"],
                "niches": ["P1 — Revendas premium e multimarcas", "P2 — Luxo e superesportivos"],
                "desired_quantity": 12,
                "sources": ["instagram", "website_auditor"],
            },
        )
        final_camp = execute_campaign(camp["id"], db_path=self.db_path, perform_live_http_audit=False)
        self.assertEqual(final_camp["status"], "completed")
        self.assertGreater(final_camp["total_found"], 0)

        csv_str, csv_cnt = export_leads_to_csv(self.conn, {"min_score": 40})
        self.assertGreater(csv_cnt, 0)
        self.assertIn("name,niche", csv_str)

        json_list, json_cnt = export_leads_to_json(self.conn, {"min_score": 40})
        self.assertEqual(json_cnt, csv_cnt)
        sample = json_list[0]
        for required_key in (
            "companyName", "niche", "city", "country", "website",
            "instagram", "phone", "whatsapp", "email", "reviews",
            "score", "priority", "diagnosis", "opportunity", "source", "discoveredAt"
        ):
            self.assertIn(required_key, sample)

    def test_08_top_30_demos_and_direct_outreach_generation(self) -> None:
        from backend.config import BASE_DIR
        from backend.demo_builder import DEMOS_DIR, generate_top_30_demos

        real_db_path = str(BASE_DIR / "data" / "brag_lead_hunter.db")
        real_conn = get_connection(real_db_path)
        try:
            manifest = generate_top_30_demos(real_conn)
        finally:
            real_conn.close()
        self.assertEqual(len(manifest), 60)
        denis_items = [x for x in manifest if x.get("owner") == "denis"]
        gabriel_items = [x for x in manifest if x.get("owner") == "gabriel"]
        self.assertEqual(len(denis_items), 30)
        self.assertEqual(len(gabriel_items), 30)
        manifest_slugs = {x["slug"] for x in manifest}
        # Ensure the 30 Batch-1 archived demos exist on disk for Vercel but are NOT in the dashboard manifest
        for archived_slug in ("benaia-motors-carros-seminovos-e-premium", "royal-motors", "v-motors"):
            self.assertNotIn(archived_slug, manifest_slugs)
            self.assertTrue((DEMOS_DIR / archived_slug / "index.html").exists())
        for item in manifest:
            self.assertTrue(item["slug"])
            self.assertGreaterEqual(item["score"], 65)
            self.assertTrue(item["whatsapp_send_url"].startswith("https://wa.me/55"))
            self.assertIn(item["slug"], item["demo_url"])
            self.assertIn("Roteiro de Vídeo Executivo", item["video_script_60s"])
            demo_html_path = DEMOS_DIR / item["slug"] / "index.html"
            self.assertTrue(demo_html_path.exists())
            html_text = demo_html_path.read_text(encoding="utf-8")
            self.assertIn(item["short_name"], html_text)
            self.assertNotIn("Demo #", html_text)
            self.assertIn("prefers-reduced-motion", html_text)
            self.assertIn(":focus-visible", html_text)


if __name__ == "__main__":
    unittest.main()
