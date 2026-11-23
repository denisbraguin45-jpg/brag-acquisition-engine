"""
SQLite Database Schema & Repository Layer for BRAG Lead Hunter.
Implements all required tables:
- COMPANIES
- CONTACTS
- SOCIAL_PROFILES
- WEBSITES
- AUDITS
- ICP_SCORES
- CAMPAIGNS
- SEARCH_HISTORY
- EXPORT_HISTORY
- SALES_EXPERIMENTS (for Agent 16)
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.config import get_config


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or get_config()["db_path"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS COMPANIES (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    normalized_name_loc TEXT NOT NULL,
    country TEXT DEFAULT 'Brasil',
    state TEXT DEFAULT '',
    city TEXT DEFAULT '',
    region TEXT DEFAULT '',
    address TEXT DEFAULT '',
    niche TEXT DEFAULT '',
    subniche TEXT DEFAULT '',
    category TEXT DEFAULT '',
    services_offered TEXT DEFAULT '[]',
    google_rating REAL,
    google_reviews_count INTEGER,
    opening_hours TEXT DEFAULT '',
    maps_url TEXT DEFAULT '',
    latitude REAL,
    longitude REAL,
    has_own_website INTEGER DEFAULT 0,
    has_instagram INTEGER DEFAULT 0,
    commercial_status TEXT DEFAULT 'icp_identificado',
    source TEXT NOT NULL,
    data_confidence TEXT DEFAULT 'high',
    discovered_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    history_log TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_companies_name_loc ON COMPANIES(normalized_name_loc);
CREATE INDEX IF NOT EXISTS idx_companies_niche ON COMPANIES(niche);
CREATE INDEX IF NOT EXISTS idx_companies_city ON COMPANIES(city);

CREATE TABLE IF NOT EXISTS CONTACTS (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES COMPANIES(id) ON DELETE CASCADE,
    phone_raw TEXT DEFAULT '',
    phone_normalized TEXT DEFAULT '',
    whatsapp TEXT DEFAULT '',
    whatsapp_verified INTEGER DEFAULT 0,
    email TEXT DEFAULT '',
    contact_page_url TEXT DEFAULT '',
    source TEXT NOT NULL,
    confidence TEXT DEFAULT 'high',
    collected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contacts_phone_norm ON CONTACTS(phone_normalized);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON CONTACTS(company_id);

CREATE TABLE IF NOT EXISTS SOCIAL_PROFILES (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES COMPANIES(id) ON DELETE CASCADE,
    platform TEXT DEFAULT 'instagram',
    username TEXT NOT NULL,
    profile_name TEXT DEFAULT '',
    profile_url TEXT DEFAULT '',
    biography TEXT DEFAULT '',
    external_url TEXT DEFAULT '',
    public_phone TEXT DEFAULT '',
    public_email TEXT DEFAULT '',
    category TEXT DEFAULT '',
    followers_count INTEGER,
    posts_count INTEGER,
    latest_post_date TEXT DEFAULT '',
    is_business_account INTEGER DEFAULT 0,
    activity_indicators TEXT DEFAULT '',
    source TEXT NOT NULL,
    confidence TEXT DEFAULT 'high',
    collected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_social_username ON SOCIAL_PROFILES(username);
CREATE INDEX IF NOT EXISTS idx_social_company ON SOCIAL_PROFILES(company_id);

CREATE TABLE IF NOT EXISTS WEBSITES (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES COMPANIES(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    link_category TEXT DEFAULT '',
    link_type TEXT DEFAULT '',
    is_own_domain INTEGER DEFAULT 0,
    http_status INTEGER,
    final_url TEXT DEFAULT '',
    source TEXT NOT NULL,
    confidence TEXT DEFAULT 'high',
    collected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_websites_domain ON WEBSITES(domain);
CREATE INDEX IF NOT EXISTS idx_websites_company ON WEBSITES(company_id);

CREATE TABLE IF NOT EXISTS AUDITS (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES COMPANIES(id) ON DELETE CASCADE,
    website_id TEXT REFERENCES WEBSITES(id) ON DELETE SET NULL,
    url_tested TEXT NOT NULL,
    http_available INTEGER DEFAULT 0,
    http_status INTEGER,
    has_https INTEGER DEFAULT 0,
    load_time_ms INTEGER,
    is_responsive INTEGER DEFAULT 0,
    presentation_quality_score INTEGER DEFAULT 0,
    offer_clarity_score INTEGER DEFAULT 0,
    has_cta INTEGER DEFAULT 0,
    has_whatsapp_button INTEGER DEFAULT 0,
    has_contact_form INTEGER DEFAULT 0,
    commercial_structure_score INTEGER DEFAULT 0,
    audit_status TEXT DEFAULT 'no_site',
    issues_found TEXT DEFAULT '[]',
    improvement_opportunities TEXT DEFAULT '[]',
    source TEXT DEFAULT 'website_auditor',
    confidence TEXT DEFAULT 'high',
    audited_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audits_company ON AUDITS(company_id);

CREATE TABLE IF NOT EXISTS ICP_SCORES (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL UNIQUE REFERENCES COMPANIES(id) ON DELETE CASCADE,
    total_score INTEGER NOT NULL,
    priority_class TEXT NOT NULL,
    pts_no_website INTEGER DEFAULT 0,
    pts_broken_website INTEGER DEFAULT 0,
    pts_high_value_services INTEGER DEFAULT 0,
    pts_reputation INTEGER DEFAULT 0,
    pts_active_instagram INTEGER DEFAULT 0,
    pts_commercial_contact INTEGER DEFAULT 0,
    pts_investment_potential INTEGER DEFAULT 0,
    justifications TEXT DEFAULT '[]',
    icp_fit_status TEXT DEFAULT '',
    data_quality_level TEXT DEFAULT '',
    need_evidence_level TEXT DEFAULT '',
    confirmed_purchase_intent TEXT DEFAULT 'Não confirmada (requer abordagem)',
    diagnosis TEXT DEFAULT '',
    opportunity_text TEXT DEFAULT '',
    commercial_pitch TEXT DEFAULT '',
    recommended_next_action TEXT DEFAULT '',
    recommended_offer TEXT DEFAULT '',
    calculated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_icp_scores_total ON ICP_SCORES(total_score);
CREATE INDEX IF NOT EXISTS idx_icp_scores_priority ON ICP_SCORES(priority_class);

CREATE TABLE IF NOT EXISTS CAMPAIGNS (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    config_json TEXT NOT NULL,
    total_found INTEGER DEFAULT 0,
    total_qualified INTEGER DEFAULT 0,
    new_records INTEGER DEFAULT 0,
    updated_records INTEGER DEFAULT 0,
    duplicates_avoided INTEGER DEFAULT 0,
    errors_log TEXT DEFAULT '[]',
    progress_log TEXT DEFAULT '[]',
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS SEARCH_HISTORY (
    id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES CAMPAIGNS(id) ON DELETE SET NULL,
    connector TEXT NOT NULL,
    query TEXT NOT NULL,
    city TEXT DEFAULT '',
    niche TEXT DEFAULT '',
    results_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    error_message TEXT DEFAULT '',
    executed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS EXPORT_HISTORY (
    id TEXT PRIMARY KEY,
    export_type TEXT NOT NULL,
    destination TEXT NOT NULL,
    filters_json TEXT DEFAULT '{}',
    records_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    details TEXT DEFAULT '',
    exported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS SALES_EXPERIMENTS (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    campaign_id TEXT REFERENCES CAMPAIGNS(id) ON DELETE SET NULL,
    niche TEXT NOT NULL,
    city TEXT DEFAULT '',
    script_variant TEXT NOT NULL,
    offer_type TEXT NOT NULL,
    leads_targeted INTEGER DEFAULT 0,
    contacts_made INTEGER DEFAULT 0,
    responses_received INTEGER DEFAULT 0,
    meetings_booked INTEGER DEFAULT 0,
    proposals_sent INTEGER DEFAULT 0,
    sales_closed INTEGER DEFAULT 0,
    revenue_brl REAL DEFAULT 0.0,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def init_db(db_path: Optional[str] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


def new_id(prefix: str = "") -> str:
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid
