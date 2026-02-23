import sqlite3
import json
from datetime import datetime
from config import Config

DB = Config.DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sector TEXT,
        website TEXT,
        monthly_budget REAL DEFAULT 0,
        products TEXT,
        google_ads_id TEXT,
        google_ads_status TEXT DEFAULT 'pending',
        target_cpa REAL,
        target_roas REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        google_campaign_id TEXT,
        name TEXT NOT NULL,
        campaign_type TEXT DEFAULT 'SEARCH',
        status TEXT DEFAULT 'PAUSED',
        daily_budget REAL,
        bid_strategy TEXT,
        target_cpa REAL,
        target_roas REAL,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        cost REAL DEFAULT 0,
        conversions REAL DEFAULT 0,
        ctr REAL DEFAULT 0,
        avg_cpc REAL DEFAULT 0,
        conv_rate REAL DEFAULT 0,
        last_synced TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ad_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER REFERENCES campaigns(id),
        google_adgroup_id TEXT,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'ENABLED',
        cpc_bid REAL,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        cost REAL DEFAULT 0,
        conversions REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_group_id INTEGER REFERENCES ad_groups(id),
        campaign_id INTEGER REFERENCES campaigns(id),
        google_keyword_id TEXT,
        text TEXT NOT NULL,
        match_type TEXT DEFAULT 'PHRASE',
        status TEXT DEFAULT 'ENABLED',
        is_negative INTEGER DEFAULT 0,
        quality_score INTEGER,
        cpc_bid REAL,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        cost REAL DEFAULT 0,
        conversions REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS strategies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        title TEXT,
        analysis TEXT,
        recommendations TEXT,
        budget_allocation TEXT,
        kpi_targets TEXT,
        action_plan TEXT,
        status TEXT DEFAULT 'draft',
        ai_model TEXT,
        tokens_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS action_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        action_type TEXT NOT NULL,
        description TEXT,
        details TEXT,
        status TEXT DEFAULT 'completed',
        severity TEXT DEFAULT 'info',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        alert_type TEXT NOT NULL,
        severity TEXT DEFAULT 'warning',
        title TEXT,
        message TEXT,
        is_resolved INTEGER DEFAULT 0,
        resolved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS performance_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        campaign_id INTEGER,
        snapshot_date DATE,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        cost REAL DEFAULT 0,
        conversions REAL DEFAULT 0,
        ctr REAL DEFAULT 0,
        avg_cpc REAL DEFAULT 0,
        cpa REAL DEFAULT 0,
        roas REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS seo_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        url TEXT,
        page_speed_score REAL,
        mobile_score REAL,
        seo_score REAL,
        accessibility_score REAL,
        issues TEXT,
        recommendations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS search_terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        campaign_id INTEGER,
        search_term TEXT,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        cost REAL DEFAULT 0,
        conversions REAL DEFAULT 0,
        is_flagged INTEGER DEFAULT 0,
        flag_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        action_type TEXT NOT NULL,
        title TEXT,
        description TEXT,
        payload TEXT,
        status TEXT DEFAULT 'pending',
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()


# ── CRUD Helpers ──

def insert(table, **kwargs):
    conn = get_conn()
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(kwargs.values()))
    last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return last_id


def fetch_all(table, where=None, params=None, order_by="id DESC", limit=100):
    conn = get_conn()
    q = f"SELECT * FROM {table}"
    if where:
        q += f" WHERE {where}"
    q += f" ORDER BY {order_by} LIMIT {limit}"
    rows = conn.execute(q, params or []).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_one(table, where, params=None):
    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM {table} WHERE {where}", params or []).fetchone()
    conn.close()
    return dict(rows) if rows else None


def update(table, set_clause, where, params=None):
    conn = get_conn()
    conn.execute(f"UPDATE {table} SET {set_clause} WHERE {where}", params or [])
    conn.commit()
    conn.close()


def delete(table, where, params=None):
    conn = get_conn()
    conn.execute(f"DELETE FROM {table} WHERE {where}", params or [])
    conn.commit()
    conn.close()


def count(table, where=None, params=None):
    conn = get_conn()
    q = f"SELECT COUNT(*) FROM {table}"
    if where:
        q += f" WHERE {where}"
    c = conn.execute(q, params or []).fetchone()[0]
    conn.close()
    return c


def log_action(client_id, action_type, description, details=None, severity="info"):
    insert("action_logs",
           client_id=client_id, action_type=action_type,
           description=description, details=json.dumps(details) if details else None,
           severity=severity)


def create_alert(client_id, alert_type, severity, title, message):
    insert("alerts",
           client_id=client_id, alert_type=alert_type,
           severity=severity, title=title, message=message)
