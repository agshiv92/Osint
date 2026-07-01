"""
Phantom Signal — Intervention Rules Engine (PRD-008)
Uses Gemini to generate specific, deployable intervention rules per fraud signal.
"""
import json
import logging
import uuid
from typing import Dict, List, Optional

from data.database import insert_intervention_rules
from utils.gemini_client import call_gemini_flash

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a fraud controls specialist at a Singapore bank (UOB). 
Your job is to write specific, actionable intervention rules in response to a detected fraud threat. 
Rules must be concrete enough that a bank's transaction monitoring team or digital banking team can implement them directly.
Rules must be categorized by type and include specific trigger conditions.
Return ONLY valid JSON — no explanation, no markdown."""

RULE_SCHEMA = {
    "rule_id": "unique string",
    "fraud_signal_id": "string",
    "rule_type": "TM_DETECTION | CUSTOMER_FRICTION | POLICY_CHANGE | ADVISORY",
    "target_layer": "TRANSACTION_MONITORING | AUTHENTICATION | CUSTOMER_COMMS | POLICY",
    "rule_description": "1-2 sentences plain English",
    "rule_logic": "IF/THEN pseudocode",
    "trigger_conditions": ["list of specific conditions"],
    "expected_impact_pct": "float 5-40",
    "deployment_risk": "LOW | MEDIUM | HIGH",
    "approval_required": "boolean",
    "auto_deployable": "boolean (true ONLY for ADVISORY + LOW risk)"
}


def _build_fallback_rules(fraud_signal: Dict, assessment: Dict) -> List[Dict]:
    """Hard-coded fallback rules if Gemini is unavailable."""
    typology = fraud_signal.get("fraud_typology", "UNKNOWN")
    fid = fraud_signal.get("fraud_signal_id", str(uuid.uuid4()))
    segment = fraud_signal.get("victim_profile", {}).get("customer_segment", "RETAIL")
    undetected = assessment.get("gate3_control_gap", {}).get("undetected_percentage", 50.0)

    return [
        {
            "rule_id": str(uuid.uuid4()),
            "fraud_signal_id": fid,
            "rule_type": "TM_DETECTION",
            "target_layer": "TRANSACTION_MONITORING",
            "rule_description": (
                f"Flag transactions matching {typology} behavioral pattern: "
                f"new payee + high-value transfer within 2 hours of suspicious login event."
            ),
            "rule_logic": (
                f"IF account receives new device login AND transfer > SGD 1,000 to new payee "
                f"WITHIN 2 hours THEN flag for {typology} review"
            ),
            "trigger_conditions": [
                "New device login event",
                "Transfer to payee added within 24 hours",
                "Transfer amount > SGD 1,000",
                "Transaction within 2 hours of login"
            ],
            "expected_impact_pct": 22.0,
            "deployment_risk": "MEDIUM",
            "approval_required": True,
            "auto_deployable": False,
        },
        {
            "rule_id": str(uuid.uuid4()),
            "fraud_signal_id": fid,
            "rule_type": "CUSTOMER_FRICTION",
            "target_layer": "AUTHENTICATION",
            "rule_description": (
                f"Add step-up authentication for {segment} customers performing high-value transfers "
                f"when {typology} indicators are present."
            ),
            "rule_logic": (
                f"IF customer_segment = {segment} AND transaction > SGD 5,000 "
                f"AND risk_score > 70 THEN require biometric re-authentication"
            ),
            "trigger_conditions": [
                f"Customer segment: {segment}",
                "Transaction value > SGD 5,000",
                "Real-time risk score > 70",
                f"{typology} behavioral pattern detected"
            ],
            "expected_impact_pct": 18.0,
            "deployment_risk": "HIGH",
            "approval_required": True,
            "auto_deployable": False,
        },
        {
            "rule_id": str(uuid.uuid4()),
            "fraud_signal_id": fid,
            "rule_type": "POLICY_CHANGE",
            "target_layer": "POLICY",
            "rule_description": (
                f"Update fraud typology playbook to include {typology} response procedures. "
                f"Assign dedicated analyst queue for alerts flagged by new TM rule."
            ),
            "rule_logic": (
                f"IF alert type = {typology} THEN route to dedicated fraud analyst queue "
                f"with 4-hour SLA; escalate to Head of Fraud Risk if unresolved"
            ),
            "trigger_conditions": [
                f"Alert typology = {typology}",
                "Composite risk score > 60",
                "No existing playbook entry",
            ],
            "expected_impact_pct": 15.0,
            "deployment_risk": "LOW",
            "approval_required": True,
            "auto_deployable": False,
        },
        {
            "rule_id": str(uuid.uuid4()),
            "fraud_signal_id": fid,
            "rule_type": "ADVISORY",
            "target_layer": "CUSTOMER_COMMS",
            "rule_description": (
                f"Issue proactive advisory to {segment} customers warning of active {typology} "
                f"campaign, with guidance on how to identify and report suspicious contacts."
            ),
            "rule_logic": (
                f"IF customer_segment IN [{segment}] AND geography IN [SG, MY] "
                f"THEN send push notification + email advisory within 24 hours"
            ),
            "trigger_conditions": [
                f"Active {typology} threat confirmed",
                f"Customer segment: {segment}",
                "Geography: SG, MY",
                "Digital channel usage: HIGH or MEDIUM"
            ],
            "expected_impact_pct": 12.0,
            "deployment_risk": "LOW",
            "approval_required": False,
            "auto_deployable": True,
        },
    ]


def generate_intervention_rules(
    fraud_signal: Dict,
    assessment: Dict,
    simulation: Optional[Dict] = None,
) -> List[Dict]:
    """
    Generate intervention rules via Gemini. Falls back to templates if Gemini fails.
    Returns list of InterventionRule dicts, persisted to database.
    """
    typology = fraud_signal.get("fraud_typology", "UNKNOWN")
    fid = fraud_signal.get("fraud_signal_id", str(uuid.uuid4()))
    segment = fraud_signal.get("victim_profile", {}).get("customer_segment", "RETAIL")
    g3 = assessment.get("gate3_control_gap", {})
    undetected_pct = g3.get("undetected_percentage", 50.0)
    auth_vuln = g3.get("auth_vulnerability", False)
    at_risk = assessment.get("gate2_customer_exposure", {}).get("estimated_at_risk_customers", 0)

    user_prompt = f"""Generate intervention rules for the following fraud threat at UOB Singapore.

FRAUD TYPOLOGY: {typology}
FRAUD DESCRIPTION: {fraud_signal.get('fraud_description', '')[:500]}
AT-RISK SEGMENTS: {segment} ({at_risk:,} customers)
UNDETECTED RATE: {undetected_pct:.0f}%
PRIMARY VULNERABLE AUTH: {"SMS_OTP (HIGH RISK)" if auth_vuln else "Mixed"}
ATTACK VECTOR: {fraud_signal.get('attack_vector', '')}

Generate rules covering ALL FOUR categories (exactly 1 rule per category):
1. TM_DETECTION — A new transaction monitoring detection rule
2. CUSTOMER_FRICTION — A friction/challenge at a specific customer interaction point
3. POLICY_CHANGE — A policy or procedural change  
4. ADVISORY — Customer advisory messaging

Return a JSON ARRAY of exactly 4 InterventionRule objects with schema:
{json.dumps(RULE_SCHEMA, indent=2)}

Rules for ADVISORY type with LOW deployment_risk ONLY may have auto_deployable=true.
Keep expected_impact_pct between 5 and 40. Be specific about trigger conditions."""

    rules_raw = None
    try:
        rules_raw = call_gemini_flash(SYSTEM_PROMPT, user_prompt, expect_json=True)
    except Exception as e:
        logger.warning("Gemini intervention rules call failed: %s — using fallback", e)

    rules = []
    if isinstance(rules_raw, list) and len(rules_raw) >= 1:
        for r in rules_raw:
            # Validate
            if not isinstance(r, dict):
                continue
            impact = float(r.get("expected_impact_pct", 10.0))
            if impact > 50:
                r["expected_impact_pct"] = 40.0
            if r.get("auto_deployable") and (
                r.get("deployment_risk") != "LOW" or r.get("rule_type") != "ADVISORY"
            ):
                r["auto_deployable"] = False
            r["rule_id"] = str(uuid.uuid4())
            r["fraud_signal_id"] = fid
            rules.append(r)

    if len(rules) < 4:
        logger.info("Using fallback intervention rules (Gemini returned %d)", len(rules))
        rules = _build_fallback_rules(fraud_signal, assessment)

    insert_intervention_rules(rules)
    logger.info("Generated %d intervention rules for %s", len(rules), fid)
    return rules
