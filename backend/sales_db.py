import json
import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path("D:/app/brag-lead-hunter/data/brag_lead_hunter.db")
DEMOS_DIR = Path("D:/app/brag-lead-hunter/demos")

def init_sales_tables(conn: sqlite3.Connection):
    c = conn.cursor()
    # 1. DISTRIBUTION TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS SALES_DISTRIBUTION (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        distributed_at TEXT NOT NULL,
        distributed_by TEXT NOT NULL,
        total_leads INTEGER NOT NULL,
        bruce_leads_count INTEGER NOT NULL,
        gabriel_leads_count INTEGER NOT NULL,
        criteria TEXT NOT NULL
    )
    """)

    # 2. SALES LEADS TABLE (Tracks assigned vendor, stages, classifications, callbacks)
    c.execute("""
    CREATE TABLE IF NOT EXISTS SALES_LEADS (
        slug TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        contact_name TEXT,
        segment TEXT,
        city TEXT,
        state TEXT,
        phone TEXT,
        whatsapp_e164 TEXT,
        instagram_username TEXT,
        instagram_url TEXT,
        website_url TEXT,
        demo_url TEXT,
        score INTEGER NOT NULL DEFAULT 90,
        priority TEXT NOT NULL DEFAULT 'A',
        potential_tier TEXT NOT NULL DEFAULT 'high', -- high, medium, low
        assigned_vendor TEXT NOT NULL, -- 'bruce' or 'gabriel'
        vendor_rank INTEGER NOT NULL,
        classification TEXT NOT NULL DEFAULT 'COLD', -- 'HOT', 'WARM', 'COLD', 'LOST'
        stage TEXT NOT NULL DEFAULT 'novo_lead', -- 'novo_lead', 'primeira_ligacao', 'decisor', 'apresentacao_demo', 'qualificacao', 'proposta', 'negociacao', 'fechamento', 'perdido'
        calls_made INTEGER NOT NULL DEFAULT 0,
        calls_answered INTEGER NOT NULL DEFAULT 0,
        decision_maker_contacted INTEGER NOT NULL DEFAULT 0,
        demo_presented INTEGER NOT NULL DEFAULT 0,
        interested INTEGER NOT NULL DEFAULT 0,
        proposal_sent INTEGER NOT NULL DEFAULT 0,
        negotiation_opened INTEGER NOT NULL DEFAULT 0,
        deal_closed INTEGER NOT NULL DEFAULT 0,
        deal_value REAL NOT NULL DEFAULT 0.0,
        last_interaction_at TEXT,
        next_action TEXT,
        scheduled_callback_at TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 3. SALES INTERACTIONS TABLE (Detailed audit log of calls, notes, proposals, objections)
    c.execute("""
    CREATE TABLE IF NOT EXISTS SALES_INTERACTIONS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL,
        vendor TEXT NOT NULL,
        interaction_type TEXT NOT NULL, -- 'call', 'script_copied', 'demo_viewed', 'status_change', 'proposal', 'callback_scheduled'
        script_used TEXT,
        call_outcome TEXT, -- 'answered', 'no_answer', 'busy', 'decision_maker', 'not_decision_maker', 'objection', 'interested', 'meeting_set'
        notes TEXT,
        next_action TEXT,
        scheduled_at TEXT,
        deal_value REAL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (slug) REFERENCES SALES_LEADS(slug)
    )
    """)

    conn.commit()
    print("Sales operation tables initialized successfully!")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    init_sales_tables(conn)
    conn.close()
