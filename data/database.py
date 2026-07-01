"""
Phantom Signal — Firestore Database Layer
Replaces SQLite with Google Cloud Firestore for cloud-native deployment.
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

from config import FIREBASE_CREDENTIALS

logger = logging.getLogger(__name__)

# Initialize Firebase only once
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin initialized with provided credentials.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")

db = firestore.client()


def init_db():
    """No-op for Firestore. Collections are created automatically."""
    logger.info("Firestore DB initialized (No-op).")


# ── Raw Signals ───────────────────────────────────────────────────────────────

def insert_raw_signal(s: dict) -> bool:
    """Insert a raw signal. Returns True if inserted, False if duplicate."""
    # Check duplicate by content_hash (in-memory for safety against index errors)
    docs = db.collection("raw_signals").where("content_hash", "==", s.get("content_hash", "")).limit(1).stream()
    if any(docs):
        return False
        
    sig_id = s["signal_id"]
    db.collection("raw_signals").document(sig_id).set({
        "signal_id": sig_id,
        "ingested_at": s["ingested_at"],
        "source_category": s.get("source_category", "REGULATORY"),
        "source_name": s["source_name"],
        "source_url": s.get("source_url", ""),
        "raw_content": s.get("raw_content", ""),
        "content_hash": s.get("content_hash", ""),
        "language": s.get("language", "en"),
        "processing_status": s.get("processing_status", "PENDING"),
        "title": s.get("title"),
        "publication_date": s.get("publication_date"),
    })
    return True


def get_raw_signals(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    docs = db.collection("raw_signals").stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        if status and d.get("processing_status") != status:
            continue
        results.append(d)
    results.sort(key=lambda x: x.get("ingested_at", ""), reverse=True)
    return results[:limit]


def update_raw_signal_status(signal_id: str, status: str):
    db.collection("raw_signals").document(signal_id).update({"processing_status": status})


def get_raw_signal_count_today() -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    docs = db.collection("raw_signals").stream()
    count = sum(1 for doc in docs if doc.to_dict().get("ingested_at", "").startswith(today))
    return count


def count_raw_signals_by_status() -> Dict[str, int]:
    docs = db.collection("raw_signals").stream()
    counts = {}
    for doc in docs:
        status = doc.to_dict().get("processing_status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return counts


# ── Fraud Signals ─────────────────────────────────────────────────────────────

def insert_fraud_signal(fs: dict):
    fs_id = fs["fraud_signal_id"]
    db.collection("fraud_signals").document(fs_id).set({
        "fraud_signal_id": fs_id,
        "raw_signal_id": fs.get("raw_signal_id"),
        "detected_at": fs["detected_at"],
        "fraud_typology": fs["fraud_typology"],
        "fraud_description": fs.get("fraud_description", ""),
        "attack_vector": fs.get("attack_vector", ""),
        "victim_profile_json": json.dumps(fs.get("victim_profile", {})),
        "financial_mechanism": fs.get("financial_mechanism"),
        "geographic_origin_json": json.dumps(fs.get("geographic_origin", [])),
        "geographic_spread_json": json.dumps(fs.get("geographic_spread", [])),
        "first_reported_globally": fs.get("first_reported_globally"),
        "severity_estimate": fs.get("severity_estimate", "MEDIUM"),
        "novelty_score": fs.get("novelty_score", 0.5),
        "confidence_score": fs.get("confidence_score", 0.5),
        "source_credibility": fs.get("source_credibility", "MEDIUM"),
        "raw_evidence": fs.get("raw_evidence"),
    })


def get_fraud_signals(typology: Optional[str] = None, severity: Optional[str] = None, limit: int = 200) -> List[Dict]:
    docs = db.collection("fraud_signals").stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        if typology and d.get("fraud_typology") != typology:
            continue
        if severity and d.get("severity_estimate") != severity:
            continue
        
        # Parse JSON fields
        for field in ["victim_profile_json", "geographic_origin_json", "geographic_spread_json"]:
            key = field.replace("_json", "")
            try:
                d[key] = json.loads(d.pop(field) or "{}") if "profile" in field else json.loads(d.pop(field) or "[]")
            except:
                d[key] = {} if "profile" in field else []
                
        results.append(d)
        
    results.sort(key=lambda x: x.get("detected_at", ""), reverse=True)
    return results[:limit]


def get_fraud_signal_by_id(fraud_signal_id: str) -> Optional[Dict]:
    doc = db.collection("fraud_signals").document(fraud_signal_id).get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    for field in ["victim_profile_json", "geographic_origin_json", "geographic_spread_json"]:
        key = field.replace("_json", "")
        try:
            d[key] = json.loads(d.pop(field, None) or "{}")
        except:
            d[key] = {}
    return d


def get_signals_by_typology_counts() -> Dict[str, int]:
    docs = db.collection("fraud_signals").stream()
    counts = {}
    for doc in docs:
        typology = doc.to_dict().get("fraud_typology", "UNKNOWN")
        counts[typology] = counts.get(typology, 0) + 1
    return counts


# ── Relevance Assessments ─────────────────────────────────────────────────────

def insert_relevance_assessment(ra: dict):
    ra_id = ra["assessment_id"]
    db.collection("relevance_assessments").document(ra_id).set({
        "assessment_id": ra_id,
        "fraud_signal_id": ra["fraud_signal_id"],
        "assessed_at": ra["assessed_at"],
        "gate1_json": json.dumps(ra.get("gate1_novelty", {})),
        "gate2_json": json.dumps(ra.get("gate2_customer_exposure", {})),
        "gate3_json": json.dumps(ra.get("gate3_control_gap", {})),
        "overall_passed": 1 if ra.get("overall_passed") else 0,
        "composite_risk_score": ra.get("composite_risk_score", 0.0),
        "alert_priority": ra.get("alert_priority", "LOW"),
        "recommended_actions_json": json.dumps(ra.get("recommended_actions", [])),
    })


def get_relevance_assessments(passed_only: bool = False, limit: int = 200) -> List[Dict]:
    docs = db.collection("relevance_assessments").stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        if passed_only and not d.get("overall_passed"):
            continue
            
        for f in ["gate1_json", "gate2_json", "gate3_json", "recommended_actions_json"]:
            key = f.replace("_json", "")
            try:
                d[key] = json.loads(d.pop(f, None) or "{}")
            except:
                d[key] = {}
        d["overall_passed"] = bool(d.get("overall_passed"))
        results.append(d)
        
    results.sort(key=lambda x: x.get("assessed_at", ""), reverse=True)
    return results[:limit]


def get_assessment_by_signal(fraud_signal_id: str) -> Optional[Dict]:
    docs = db.collection("relevance_assessments").where("fraud_signal_id", "==", fraud_signal_id).stream()
    # Sort in memory since where + order_by might need composite index
    results = []
    for doc in docs:
        d = doc.to_dict()
        for f in ["gate1_json", "gate2_json", "gate3_json", "recommended_actions_json"]:
            key = f.replace("_json", "")
            try:
                d[key] = json.loads(d.pop(f, None) or "{}")
            except:
                d[key] = {}
        d["overall_passed"] = bool(d.get("overall_passed"))
        results.append(d)
        
    results.sort(key=lambda x: x.get("assessed_at", ""), reverse=True)
    return results[0] if results else None


# ── Simulations ───────────────────────────────────────────────────────────────

def insert_simulation(sim: dict):
    sim_id = sim["simulation_id"]
    db.collection("simulations").document(sim_id).set({
        "simulation_id": sim_id,
        "fraud_signal_id": sim["fraud_signal_id"],
        "run_at": sim["run_at"],
        "scenario_name": sim.get("scenario_name", ""),
        "customer_exposure_json": json.dumps(sim.get("customer_exposure", {})),
        "financial_impact_json": json.dumps(sim.get("financial_impact", {})),
        "control_gap_json": json.dumps(sim.get("control_gap_analysis", {})),
        "interventions_json": json.dumps(sim.get("proposed_interventions", [])),
    })


def get_simulation_by_signal(fraud_signal_id: str) -> Optional[Dict]:
    docs = db.collection("simulations").where("fraud_signal_id", "==", fraud_signal_id).stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        for f in ["customer_exposure_json", "financial_impact_json", "control_gap_json", "interventions_json"]:
            key = f.replace("_json", "")
            try:
                d[key] = json.loads(d.pop(f, None) or "{}")
            except:
                d[key] = {}
        results.append(d)
        
    results.sort(key=lambda x: x.get("run_at", ""), reverse=True)
    return results[0] if results else None


# ── Risk Alerts ───────────────────────────────────────────────────────────────

def insert_risk_alert(alert: dict):
    alert_id = alert["alert_id"]
    db.collection("risk_alerts").document(alert_id).set({
        "alert_id": alert_id,
        "fraud_signal_id": alert["fraud_signal_id"],
        "assessment_id": alert.get("assessment_id"),
        "simulation_id": alert.get("simulation_id"),
        "generated_at": alert["generated_at"],
        "priority": alert.get("priority", "LOW"),
        "document_json": json.dumps(alert.get("document", {})),
        "routing_json": json.dumps(alert.get("routing", {})),
        "pdf_path": alert.get("pdf_path"),
    })
    
    db.collection("alert_log").document(alert_id).set({
        "alert_id": alert_id,
        "generated_at": alert["generated_at"],
        "priority": alert.get("priority", "LOW"),
        "fraud_typology": alert.get("fraud_typology", ""),
        "composite_score": alert.get("composite_score", 0.0),
        "pdf_path": alert.get("pdf_path"),
    })


def get_risk_alerts(limit: int = 100) -> List[Dict]:
    docs = db.collection("risk_alerts").stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        for f in ["document_json", "routing_json"]:
            key = f.replace("_json", "")
            try:
                d[key] = json.loads(d.pop(f, None) or "{}")
            except:
                d[key] = {}
        results.append(d)
        
    results.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
    return results[:limit]


def get_alert_by_id(alert_id: str) -> Optional[Dict]:
    doc = db.collection("risk_alerts").document(alert_id).get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    for f in ["document_json", "routing_json"]:
        key = f.replace("_json", "")
        try:
            d[key] = json.loads(d.pop(f, None) or "{}")
        except:
            d[key] = {}
    return d


def get_alerts_count_today() -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    docs = db.collection("risk_alerts").stream()
    count = sum(1 for doc in docs if doc.to_dict().get("generated_at", "").startswith(today))
    return count


# ── Intervention Rules ────────────────────────────────────────────────────────

def insert_intervention_rules(rules: List[dict]):
    batch = db.batch()
    for r in rules:
        doc_ref = db.collection("intervention_rules").document(r["rule_id"])
        batch.set(doc_ref, {
            "rule_id": r["rule_id"],
            "fraud_signal_id": r["fraud_signal_id"],
            "rule_type": r["rule_type"],
            "target_layer": r.get("target_layer", ""),
            "rule_description": r.get("rule_description", ""),
            "rule_logic": r.get("rule_logic", ""),
            "trigger_conditions_json": json.dumps(r.get("trigger_conditions", [])),
            "expected_impact_pct": r.get("expected_impact_pct", 10.0),
            "deployment_risk": r.get("deployment_risk", "MEDIUM"),
            "approval_required": 1 if r.get("approval_required", True) else 0,
            "auto_deployable": 1 if r.get("auto_deployable", False) else 0,
        })
    batch.commit()


def get_intervention_rules(fraud_signal_id: str) -> List[Dict]:
    docs = db.collection("intervention_rules").where("fraud_signal_id", "==", fraud_signal_id).stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        try:
            d["trigger_conditions"] = json.loads(d.pop("trigger_conditions_json", None) or "[]")
        except:
            d["trigger_conditions"] = []
        d["approval_required"] = bool(d.get("approval_required"))
        d["auto_deployable"] = bool(d.get("auto_deployable"))
        results.append(d)
    return results


# ── Synthetic Data ────────────────────────────────────────────────────────────

def _delete_collection(collection_name: str, batch_size: int = 100):
    coll_ref = db.collection(collection_name)
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0
    for doc in docs:
        doc.reference.delete()
        deleted += 1
    if deleted >= batch_size:
        return _delete_collection(collection_name, batch_size)


def insert_customer_personas(personas: List[dict]):
    _delete_collection("mock_customer_personas")
    
    # Firestore batches allow max 500 ops. Personas could be 500k in PRD-003, but in SQLite it was just a few dozen aggregated summaries.
    batch = db.batch()
    count = 0
    for p in personas:
        doc_ref = db.collection("mock_customer_personas").document(p["persona_id"])
        batch.set(doc_ref, {
            "persona_id": p["persona_id"],
            "segment": p["segment"],
            "sub_segment": p.get("sub_segment", ""),
            "geography": p["geography"],
            "age_band": p.get("age_band", "26-35"),
            "digital_channel_usage": p.get("digital_channel_usage", "MEDIUM"),
            "auth_method": p.get("auth_method", "SMS_OTP"),
            "avg_transaction_amount_sgd": p.get("avg_transaction_amount_sgd", 500.0),
            "monthly_transaction_count": p.get("monthly_transaction_count", 10),
            "risk_rating": p.get("risk_rating", "LOW"),
            "population_count": p.get("population_count", 0),
        })
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
    if count % 400 != 0:
        batch.commit()


def insert_tm_rules(rules: List[dict]):
    _delete_collection("mock_tm_rules")
    batch = db.batch()
    for r in rules:
        doc_ref = db.collection("mock_tm_rules").document(r["rule_id"])
        batch.set(doc_ref, {
            "rule_id": r["rule_id"],
            "rule_name": r["rule_name"],
            "fraud_typologies_json": json.dumps(r.get("fraud_typologies_targeted", [])),
            "detection_trigger": r.get("detection_trigger", ""),
            "threshold_description": r.get("threshold_description", ""),
            "channel_coverage_json": json.dumps(r.get("channel_coverage", [])),
            "estimated_catch_rate_pct": r.get("estimated_catch_rate_pct", 50.0),
            "last_updated": r.get("last_updated", ""),
            "active": 1 if r.get("active", True) else 0,
        })
    batch.commit()


def insert_fraud_history(incidents: List[dict]):
    _delete_collection("mock_fraud_history")
    batch = db.batch()
    count = 0
    for i in incidents:
        doc_ref = db.collection("mock_fraud_history").document(i["incident_id"])
        batch.set(doc_ref, {
            "incident_id": i["incident_id"],
            "fraud_typology": i["fraud_typology"],
            "detection_date": i.get("detection_date", ""),
            "loss_amount_sgd": i.get("loss_amount_sgd", 0.0),
            "customer_segment": i.get("customer_segment", "RETAIL"),
            "geography": i.get("geography", "SG"),
            "detection_method": i.get("detection_method", ""),
            "resolution_days": i.get("resolution_days", 30),
            "was_recovered": 1 if i.get("was_recovered", False) else 0,
            "recovery_amount_sgd": i.get("recovery_amount_sgd", 0.0),
        })
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
    if count % 400 != 0:
        batch.commit()


def get_tm_rules() -> List[Dict]:
    docs = db.collection("mock_tm_rules").where("active", "==", 1).stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        for f in ["fraud_typologies_json", "channel_coverage_json"]:
            key = f.replace("_json", "")
            try:
                d[key] = json.loads(d.pop(f, None) or "[]")
            except:
                d[key] = []
        d["active"] = bool(d["active"])
        results.append(d)
    return results


def get_customer_personas(segment: Optional[str] = None, geography: Optional[str] = None, auth_method: Optional[str] = None) -> List[Dict]:
    docs = db.collection("mock_customer_personas").stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        if segment and d.get("segment") != segment: continue
        if geography and d.get("geography") != geography: continue
        if auth_method and d.get("auth_method") != auth_method: continue
        results.append(d)
    return results


def get_fraud_history_by_typology(typology: str) -> List[Dict]:
    docs = db.collection("mock_fraud_history").where("fraud_typology", "==", typology).stream()
    return [doc.to_dict() for doc in docs]


# ── Seed Control ──────────────────────────────────────────────────────────────

def is_seeded(key: str) -> bool:
    doc = db.collection("seed_control").document(key).get()
    return doc.exists and doc.to_dict().get("value") == "done"


def mark_seeded(key: str):
    db.collection("seed_control").document(key).set({"value": "done"})


# ── LLM Usage Log ─────────────────────────────────────────────────────────────

def log_llm_usage(model: str, input_tokens: int, output_tokens: int, operation: str):
    db.collection("llm_usage_log").add({
        "timestamp": datetime.utcnow().isoformat(),
        "model_name": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "operation": operation
    })


# ── Ingestion Error Log ───────────────────────────────────────────────────────

def log_ingestion_error(source_name: str, error_msg: str, source_url: str = ""):
    db.collection("ingestion_errors").add({
        "timestamp": datetime.utcnow().isoformat(),
        "source_name": source_name,
        "error_msg": error_msg,
        "source_url": source_url
    })
