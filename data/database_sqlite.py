"""
Phantom Signal — SQLite Database Layer
Replaces Google BigQuery for local demo. All tables mirror PRD-010 schema.
"""
import sqlite3
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from config import DB_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_conn():
    """Context manager for SQLite connection with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables. Safe to call multiple times (idempotent)."""
    with get_conn() as conn:
        conn.executescript("""
        -- Raw signals from OSInt sources
        CREATE TABLE IF NOT EXISTS raw_signals (
            signal_id         TEXT PRIMARY KEY,
            ingested_at       TEXT NOT NULL,
            source_category   TEXT NOT NULL DEFAULT 'REGULATORY',
            source_name       TEXT NOT NULL,
            source_url        TEXT NOT NULL,
            raw_content       TEXT NOT NULL DEFAULT '',
            content_hash      TEXT,
            language          TEXT DEFAULT 'en',
            processing_status TEXT DEFAULT 'PENDING',
            title             TEXT,
            publication_date  TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_raw_signals_status  ON raw_signals(processing_status);
        CREATE INDEX IF NOT EXISTS idx_raw_signals_hash    ON raw_signals(content_hash);
        CREATE INDEX IF NOT EXISTS idx_raw_signals_time    ON raw_signals(ingested_at);

        -- Normalized fraud signals
        CREATE TABLE IF NOT EXISTS fraud_signals (
            fraud_signal_id          TEXT PRIMARY KEY,
            raw_signal_id            TEXT,
            detected_at              TEXT NOT NULL,
            fraud_typology           TEXT NOT NULL,
            fraud_description        TEXT,
            attack_vector            TEXT,
            victim_profile_json      TEXT,
            financial_mechanism      TEXT,
            geographic_origin_json   TEXT,
            geographic_spread_json   TEXT,
            first_reported_globally  TEXT,
            severity_estimate        TEXT DEFAULT 'MEDIUM',
            novelty_score            REAL DEFAULT 0.5,
            confidence_score         REAL DEFAULT 0.5,
            source_credibility       TEXT DEFAULT 'MEDIUM',
            raw_evidence             TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_fraud_signals_typology  ON fraud_signals(fraud_typology);
        CREATE INDEX IF NOT EXISTS idx_fraud_signals_severity  ON fraud_signals(severity_estimate);
        CREATE INDEX IF NOT EXISTS idx_fraud_signals_time      ON fraud_signals(detected_at);

        -- 3-gate relevance assessments
        CREATE TABLE IF NOT EXISTS relevance_assessments (
            assessment_id        TEXT PRIMARY KEY,
            fraud_signal_id      TEXT NOT NULL,
            assessed_at          TEXT NOT NULL,
            gate1_json           TEXT,
            gate2_json           TEXT,
            gate3_json           TEXT,
            overall_passed       INTEGER DEFAULT 0,
            composite_risk_score REAL DEFAULT 0.0,
            alert_priority       TEXT DEFAULT 'LOW',
            recommended_actions_json TEXT
        );

        -- Simulation results
        CREATE TABLE IF NOT EXISTS simulations (
            simulation_id        TEXT PRIMARY KEY,
            fraud_signal_id      TEXT NOT NULL,
            run_at               TEXT NOT NULL,
            scenario_name        TEXT,
            customer_exposure_json TEXT,
            financial_impact_json  TEXT,
            control_gap_json       TEXT,
            interventions_json     TEXT
        );

        -- Risk alert documents
        CREATE TABLE IF NOT EXISTS risk_alerts (
            alert_id         TEXT PRIMARY KEY,
            fraud_signal_id  TEXT NOT NULL,
            assessment_id    TEXT,
            simulation_id    TEXT,
            generated_at     TEXT NOT NULL,
            priority         TEXT DEFAULT 'LOW',
            document_json    TEXT,
            routing_json     TEXT,
            pdf_path         TEXT
        );

        -- Intervention rules
        CREATE TABLE IF NOT EXISTS intervention_rules (
            rule_id               TEXT PRIMARY KEY,
            fraud_signal_id       TEXT NOT NULL,
            rule_type             TEXT NOT NULL,
            target_layer          TEXT,
            rule_description      TEXT,
            rule_logic            TEXT,
            trigger_conditions_json TEXT,
            expected_impact_pct   REAL DEFAULT 10.0,
            deployment_risk       TEXT DEFAULT 'MEDIUM',
            approval_required     INTEGER DEFAULT 1,
            auto_deployable       INTEGER DEFAULT 0
        );

        -- Synthetic customer personas (aggregated)
        CREATE TABLE IF NOT EXISTS mock_customer_personas (
            persona_id                  TEXT PRIMARY KEY,
            segment                     TEXT NOT NULL,
            sub_segment                 TEXT,
            geography                   TEXT NOT NULL,
            age_band                    TEXT,
            digital_channel_usage       TEXT DEFAULT 'MEDIUM',
            auth_method                 TEXT DEFAULT 'SMS_OTP',
            avg_transaction_amount_sgd  REAL DEFAULT 500.0,
            monthly_transaction_count   INTEGER DEFAULT 10,
            risk_rating                 TEXT DEFAULT 'LOW',
            population_count            INTEGER DEFAULT 0
        );

        -- Synthetic TM rules
        CREATE TABLE IF NOT EXISTS mock_tm_rules (
            rule_id                     TEXT PRIMARY KEY,
            rule_name                   TEXT NOT NULL,
            fraud_typologies_json       TEXT,
            detection_trigger           TEXT,
            threshold_description       TEXT,
            channel_coverage_json       TEXT,
            estimated_catch_rate_pct    REAL DEFAULT 50.0,
            last_updated                TEXT,
            active                      INTEGER DEFAULT 1
        );

        -- Synthetic fraud history
        CREATE TABLE IF NOT EXISTS mock_fraud_history (
            incident_id        TEXT PRIMARY KEY,
            fraud_typology     TEXT NOT NULL,
            detection_date     TEXT,
            loss_amount_sgd    REAL,
            customer_segment   TEXT,
            geography          TEXT,
            detection_method   TEXT,
            resolution_days    INTEGER,
            was_recovered      INTEGER DEFAULT 0,
            recovery_amount_sgd REAL DEFAULT 0.0
        );

        -- Ingestion error log
        CREATE TABLE IF NOT EXISTS ingestion_errors (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT NOT NULL,
            source_name TEXT,
            error_msg  TEXT,
            source_url TEXT
        );

        -- LLM usage log
        CREATE TABLE IF NOT EXISTS llm_usage_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT NOT NULL,
            model_name   TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            operation    TEXT
        );

        -- Alert summary log
        CREATE TABLE IF NOT EXISTS alert_log (
            alert_id      TEXT PRIMARY KEY,
            generated_at  TEXT NOT NULL,
            priority      TEXT,
            fraud_typology TEXT,
            composite_score REAL,
            pdf_path      TEXT
        );

        -- Seeding control
        CREATE TABLE IF NOT EXISTS seed_control (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """)
    logger.info("Database initialized at %s", DB_PATH)


# ── Raw Signals ───────────────────────────────────────────────────────────────

def insert_raw_signal(s: dict) -> bool:
    """Insert a raw signal. Returns True if inserted, False if duplicate."""
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT 1 FROM raw_signals WHERE content_hash = ?", (s.get("content_hash",""),)
        ).fetchone()
        if existing:
            return False
        conn.execute("""
            INSERT OR REPLACE INTO raw_signals
            (signal_id, ingested_at, source_category, source_name, source_url,
             raw_content, content_hash, language, processing_status, title, publication_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            s["signal_id"], s["ingested_at"], s.get("source_category","REGULATORY"),
            s["source_name"], s.get("source_url",""), s.get("raw_content",""),
            s.get("content_hash",""), s.get("language","en"),
            s.get("processing_status","PENDING"), s.get("title"), s.get("publication_date"),
        ))
        return True


def get_raw_signals(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM raw_signals WHERE processing_status=? ORDER BY ingested_at DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM raw_signals ORDER BY ingested_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


def update_raw_signal_status(signal_id: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE raw_signals SET processing_status=? WHERE signal_id=?", (status, signal_id)
        )


def get_raw_signal_count_today() -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM raw_signals WHERE ingested_at LIKE ?", (f"{today}%",)
        ).fetchone()
    return row[0] if row else 0


def count_raw_signals_by_status() -> Dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT processing_status, COUNT(*) as cnt FROM raw_signals GROUP BY processing_status"
        ).fetchall()
    return {r["processing_status"]: r["cnt"] for r in rows}


# ── Fraud Signals ─────────────────────────────────────────────────────────────

def insert_fraud_signal(fs: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO fraud_signals
            (fraud_signal_id, raw_signal_id, detected_at, fraud_typology,
             fraud_description, attack_vector, victim_profile_json, financial_mechanism,
             geographic_origin_json, geographic_spread_json, first_reported_globally,
             severity_estimate, novelty_score, confidence_score, source_credibility, raw_evidence)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            fs["fraud_signal_id"], fs.get("raw_signal_id"), fs["detected_at"],
            fs["fraud_typology"], fs.get("fraud_description",""), fs.get("attack_vector",""),
            json.dumps(fs.get("victim_profile", {})),
            fs.get("financial_mechanism"),
            json.dumps(fs.get("geographic_origin", [])),
            json.dumps(fs.get("geographic_spread", [])),
            fs.get("first_reported_globally"),
            fs.get("severity_estimate","MEDIUM"),
            fs.get("novelty_score", 0.5), fs.get("confidence_score", 0.5),
            fs.get("source_credibility","MEDIUM"), fs.get("raw_evidence"),
        ))


def get_fraud_signals(typology: Optional[str] = None,
                      severity: Optional[str] = None,
                      limit: int = 200) -> List[Dict]:
    query = "SELECT * FROM fraud_signals WHERE 1=1"
    params: List[Any] = []
    if typology:
        query += " AND fraud_typology=?"
        params.append(typology)
    if severity:
        query += " AND severity_estimate=?"
        params.append(severity)
    query += " ORDER BY detected_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        for field in ["victim_profile_json","geographic_origin_json","geographic_spread_json"]:
            key = field.replace("_json","")
            try:
                d[key] = json.loads(d.pop(field) or "[]")
            except Exception:
                d[key] = {}
        result.append(d)
    return result


def get_fraud_signal_by_id(fraud_signal_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM fraud_signals WHERE fraud_signal_id=?", (fraud_signal_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    for field in ["victim_profile_json","geographic_origin_json","geographic_spread_json"]:
        key = field.replace("_json","")
        try:
            d[key] = json.loads(d.pop(field) or "[]")
        except Exception:
            d[key] = {}
    return d


def get_signals_by_typology_counts() -> Dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT fraud_typology, COUNT(*) as cnt FROM fraud_signals GROUP BY fraud_typology ORDER BY cnt DESC"
        ).fetchall()
    return {r["fraud_typology"]: r["cnt"] for r in rows}


# ── Relevance Assessments ─────────────────────────────────────────────────────

def insert_relevance_assessment(ra: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO relevance_assessments
            (assessment_id, fraud_signal_id, assessed_at, gate1_json, gate2_json, gate3_json,
             overall_passed, composite_risk_score, alert_priority, recommended_actions_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            ra["assessment_id"], ra["fraud_signal_id"], ra["assessed_at"],
            json.dumps(ra.get("gate1_novelty",{})),
            json.dumps(ra.get("gate2_customer_exposure",{})),
            json.dumps(ra.get("gate3_control_gap",{})),
            1 if ra.get("overall_passed") else 0,
            ra.get("composite_risk_score", 0.0),
            ra.get("alert_priority","LOW"),
            json.dumps(ra.get("recommended_actions",[])),
        ))


def get_relevance_assessments(passed_only: bool = False, limit: int = 200) -> List[Dict]:
    query = "SELECT * FROM relevance_assessments WHERE 1=1"
    params: List[Any] = []
    if passed_only:
        query += " AND overall_passed=1"
    query += " ORDER BY assessed_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        for f in ["gate1_json","gate2_json","gate3_json","recommended_actions_json"]:
            key = f.replace("_json","")
            try:
                d[key] = json.loads(d.pop(f) or "{}")
            except Exception:
                d[key] = {}
        d["overall_passed"] = bool(d["overall_passed"])
        result.append(d)
    return result


def get_assessment_by_signal(fraud_signal_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM relevance_assessments WHERE fraud_signal_id=? ORDER BY assessed_at DESC LIMIT 1",
            (fraud_signal_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    for f in ["gate1_json","gate2_json","gate3_json","recommended_actions_json"]:
        key = f.replace("_json","")
        try:
            d[key] = json.loads(d.pop(f) or "{}")
        except Exception:
            d[key] = {}
    d["overall_passed"] = bool(d["overall_passed"])
    return d


# ── Simulations ───────────────────────────────────────────────────────────────

def insert_simulation(sim: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO simulations
            (simulation_id, fraud_signal_id, run_at, scenario_name,
             customer_exposure_json, financial_impact_json, control_gap_json, interventions_json)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            sim["simulation_id"], sim["fraud_signal_id"], sim["run_at"],
            sim.get("scenario_name",""),
            json.dumps(sim.get("customer_exposure",{})),
            json.dumps(sim.get("financial_impact",{})),
            json.dumps(sim.get("control_gap_analysis",{})),
            json.dumps(sim.get("proposed_interventions",[])),
        ))


def get_simulation_by_signal(fraud_signal_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM simulations WHERE fraud_signal_id=? ORDER BY run_at DESC LIMIT 1",
            (fraud_signal_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    for f in ["customer_exposure_json","financial_impact_json","control_gap_json","interventions_json"]:
        key = f.replace("_json","")
        try:
            d[key] = json.loads(d.pop(f) or "{}")
        except Exception:
            d[key] = {}
    return d


# ── Risk Alerts ───────────────────────────────────────────────────────────────

def insert_risk_alert(alert: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO risk_alerts
            (alert_id, fraud_signal_id, assessment_id, simulation_id,
             generated_at, priority, document_json, routing_json, pdf_path)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            alert["alert_id"], alert["fraud_signal_id"],
            alert.get("assessment_id"), alert.get("simulation_id"),
            alert["generated_at"], alert.get("priority","LOW"),
            json.dumps(alert.get("document",{})),
            json.dumps(alert.get("routing",{})),
            alert.get("pdf_path"),
        ))
        conn.execute("""
            INSERT OR REPLACE INTO alert_log
            (alert_id, generated_at, priority, fraud_typology, composite_score, pdf_path)
            VALUES (?,?,?,?,?,?)
        """, (
            alert["alert_id"], alert["generated_at"],
            alert.get("priority","LOW"),
            alert.get("fraud_typology",""),
            alert.get("composite_score", 0.0),
            alert.get("pdf_path"),
        ))


def get_risk_alerts(limit: int = 100) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM risk_alerts ORDER BY generated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        for f in ["document_json","routing_json"]:
            key = f.replace("_json","")
            try:
                d[key] = json.loads(d.pop(f) or "{}")
            except Exception:
                d[key] = {}
        result.append(d)
    return result


def get_alert_by_id(alert_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM risk_alerts WHERE alert_id=?", (alert_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    for f in ["document_json","routing_json"]:
        key = f.replace("_json","")
        try:
            d[key] = json.loads(d.pop(f) or "{}")
        except Exception:
            d[key] = {}
    return d


def get_alerts_count_today() -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM risk_alerts WHERE generated_at LIKE ?", (f"{today}%",)
        ).fetchone()
    return row[0] if row else 0


# ── Intervention Rules ────────────────────────────────────────────────────────

def insert_intervention_rules(rules: List[dict]):
    with get_conn() as conn:
        for r in rules:
            conn.execute("""
                INSERT OR REPLACE INTO intervention_rules
                (rule_id, fraud_signal_id, rule_type, target_layer, rule_description,
                 rule_logic, trigger_conditions_json, expected_impact_pct,
                 deployment_risk, approval_required, auto_deployable)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r["rule_id"], r["fraud_signal_id"], r["rule_type"],
                r.get("target_layer",""), r.get("rule_description",""),
                r.get("rule_logic",""),
                json.dumps(r.get("trigger_conditions",[])),
                r.get("expected_impact_pct",10.0),
                r.get("deployment_risk","MEDIUM"),
                1 if r.get("approval_required",True) else 0,
                1 if r.get("auto_deployable",False) else 0,
            ))


def get_intervention_rules(fraud_signal_id: str) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM intervention_rules WHERE fraud_signal_id=?", (fraud_signal_id,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["trigger_conditions"] = json.loads(d.pop("trigger_conditions_json") or "[]")
        except Exception:
            d["trigger_conditions"] = []
        d["approval_required"] = bool(d["approval_required"])
        d["auto_deployable"] = bool(d["auto_deployable"])
        result.append(d)
    return result


# ── Synthetic Data ────────────────────────────────────────────────────────────

def insert_customer_personas(personas: List[dict]):
    with get_conn() as conn:
        conn.execute("DELETE FROM mock_customer_personas")
        conn.executemany("""
            INSERT INTO mock_customer_personas
            (persona_id, segment, sub_segment, geography, age_band,
             digital_channel_usage, auth_method, avg_transaction_amount_sgd,
             monthly_transaction_count, risk_rating, population_count)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, [(
            p["persona_id"], p["segment"], p.get("sub_segment",""),
            p["geography"], p.get("age_band","26-35"),
            p.get("digital_channel_usage","MEDIUM"), p.get("auth_method","SMS_OTP"),
            p.get("avg_transaction_amount_sgd",500.0),
            p.get("monthly_transaction_count",10),
            p.get("risk_rating","LOW"), p.get("population_count",0),
        ) for p in personas])


def insert_tm_rules(rules: List[dict]):
    with get_conn() as conn:
        conn.execute("DELETE FROM mock_tm_rules")
        conn.executemany("""
            INSERT INTO mock_tm_rules
            (rule_id, rule_name, fraud_typologies_json, detection_trigger,
             threshold_description, channel_coverage_json, estimated_catch_rate_pct,
             last_updated, active)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, [(
            r["rule_id"], r["rule_name"],
            json.dumps(r.get("fraud_typologies_targeted",[])),
            r.get("detection_trigger",""),
            r.get("threshold_description",""),
            json.dumps(r.get("channel_coverage",[])),
            r.get("estimated_catch_rate_pct",50.0),
            r.get("last_updated",""), 1 if r.get("active",True) else 0,
        ) for r in rules])


def insert_fraud_history(incidents: List[dict]):
    with get_conn() as conn:
        conn.execute("DELETE FROM mock_fraud_history")
        conn.executemany("""
            INSERT INTO mock_fraud_history
            (incident_id, fraud_typology, detection_date, loss_amount_sgd,
             customer_segment, geography, detection_method, resolution_days,
             was_recovered, recovery_amount_sgd)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, [(
            i["incident_id"], i["fraud_typology"], i.get("detection_date",""),
            i.get("loss_amount_sgd",0.0), i.get("customer_segment","RETAIL"),
            i.get("geography","SG"), i.get("detection_method",""),
            i.get("resolution_days",30),
            1 if i.get("was_recovered",False) else 0,
            i.get("recovery_amount_sgd",0.0),
        ) for i in incidents])


def get_tm_rules() -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM mock_tm_rules WHERE active=1"
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        for f in ["fraud_typologies_json","channel_coverage_json"]:
            key = f.replace("_json","")
            try:
                d[key] = json.loads(d.pop(f) or "[]")
            except Exception:
                d[key] = []
        d["active"] = bool(d["active"])
        result.append(d)
    return result


def get_customer_personas(segment: Optional[str] = None,
                          geography: Optional[str] = None,
                          auth_method: Optional[str] = None) -> List[Dict]:
    query = "SELECT * FROM mock_customer_personas WHERE 1=1"
    params: List[Any] = []
    if segment:
        query += " AND segment=?"
        params.append(segment)
    if geography:
        query += " AND geography=?"
        params.append(geography)
    if auth_method:
        query += " AND auth_method=?"
        params.append(auth_method)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_fraud_history_by_typology(typology: str) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM mock_fraud_history WHERE fraud_typology=?", (typology,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Seed Control ──────────────────────────────────────────────────────────────

def is_seeded(key: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM seed_control WHERE key=?", (key,)).fetchone()
    return row is not None and row["value"] == "done"


def mark_seeded(key: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO seed_control (key, value) VALUES (?, 'done')", (key,)
        )


# ── LLM Usage Log ─────────────────────────────────────────────────────────────

def log_llm_usage(model: str, input_tokens: int, output_tokens: int, operation: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO llm_usage_log (timestamp, model_name, input_tokens, output_tokens, operation)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), model, input_tokens, output_tokens, operation))


# ── Ingestion Error Log ───────────────────────────────────────────────────────

def log_ingestion_error(source_name: str, error_msg: str, source_url: str = ""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO ingestion_errors (timestamp, source_name, error_msg, source_url)
            VALUES (?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), source_name, error_msg, source_url))
