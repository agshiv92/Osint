"""
Phantom Signal — Risk Alert Document Generator (PRD-007)
Uses Gemini to generate structured professional Risk Alert Documents.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from config import TYPOLOGY_LABELS, COLOR_CRITICAL, COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW
from data.database import insert_risk_alert
from pipeline.intervention import generate_intervention_rules
from utils.gemini_client import call_gemini
from utils.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior fraud intelligence analyst at UOB, a major Singapore bank. 
You write precise, structured risk intelligence alerts for compliance leadership. 
Your writing is clear, concise, and action-oriented. You never use vague language. 
You always quantify impact in SGD where data is available. 
You write for two audiences: a senior executive (reads only Executive Summary) and a fraud analyst (reads the full document).
Return ONLY valid JSON matching the schema provided. Do not include explanation or markdown."""


def _format_sgd(amount: float) -> str:
    if amount >= 1_000_000:
        return f"SGD {amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"SGD {amount/1_000:.0f}K"
    return f"SGD {amount:.0f}"


def _build_routing(priority: str, typology: str) -> Dict:
    segment = ""
    if "RETAIL" in typology or typology in [
        "SMS_SPOOFING","SEXTORTION","PHISHING_EMAIL","INVESTMENT_SCAM","ROMANCE_SCAM"
    ]:
        segment = "RETAIL"
    elif typology in ["DEEPFAKE_CFO_FRAUD","TRADE_BASED_MONEY_LAUNDERING","BEC_CEO_FRAUD"]:
        segment = "TRADE_FINANCE"

    if priority == "CRITICAL":
        return {"compliance_team": True, "fraud_risk_team": True,
                "tm_analytics_team": True, "policy_controls_team": True}
    elif priority == "HIGH" and segment == "RETAIL":
        return {"compliance_team": True, "fraud_risk_team": True,
                "tm_analytics_team": True, "policy_controls_team": False}
    elif priority == "HIGH" and segment == "TRADE_FINANCE":
        return {"compliance_team": True, "fraud_risk_team": True,
                "tm_analytics_team": False, "policy_controls_team": True}
    elif priority == "MEDIUM":
        return {"compliance_team": False, "fraud_risk_team": True,
                "tm_analytics_team": False, "policy_controls_team": False}
    return {"compliance_team": False, "fraud_risk_team": False,
            "tm_analytics_team": True, "policy_controls_team": False}


def _build_fallback_document(
    fraud_signal: Dict,
    assessment: Dict,
    simulation: Optional[Dict],
    rules: List[Dict],
    priority: str,
) -> Dict:
    """Template-based fallback document if Gemini is unavailable."""
    typology = fraud_signal.get("fraud_typology", "UNKNOWN")
    label = TYPOLOGY_LABELS.get(typology, typology)
    segment = fraud_signal.get("victim_profile", {}).get("customer_segment", "RETAIL")
    at_risk = assessment.get("gate2_customer_exposure", {}).get("estimated_at_risk_customers", 0)
    score = assessment.get("composite_risk_score", 0.0)
    geos = fraud_signal.get("geographic_origin", ["SG"])

    sim_text = "Simulation not run."
    if simulation:
        fi = simulation.get("financial_impact", {})
        baseline = fi.get("baseline_exposure_sgd", 0)
        with_controls = fi.get("with_current_controls_sgd", 0)
        with_proposed = fi.get("with_proposed_controls_sgd", 0)
        p10 = fi.get("p10_sgd", 0)
        p90 = fi.get("p90_sgd", 0)
        sim_text = (
            f"Baseline exposure (no intervention): {_format_sgd(baseline)}. "
            f"With current controls: {_format_sgd(with_controls)}. "
            f"With proposed interventions: {_format_sgd(with_proposed)}. "
            f"Monte Carlo range (P10–P90): {_format_sgd(p10)} – {_format_sgd(p90)}."
        )

    return {
        "executive_summary": (
            f"A {priority} priority {label} threat has been identified affecting UOB's {segment} customer segment. "
            f"Approximately {at_risk:,} customers are estimated at risk across {', '.join(geos[:3])}. "
            f"Current transaction monitoring controls leave a significant detection gap, requiring immediate attention. "
            f"Immediate action: issue customer advisory and escalate to Fraud Risk for TM rule deployment."
        ),
        "threat_description": (
            f"{label} attacks exploit {fraud_signal.get('attack_vector', 'social engineering')} "
            f"to compromise customer accounts and execute unauthorized transactions. "
            f"{fraud_signal.get('fraud_description', '')} "
            f"This typology was first reported in {', '.join(geos[:2])} and has been escalating across the region."
        ),
        "uob_relevance": (
            f"UOB's {segment} customer base in Singapore and the ASEAN region is directly targeted by this fraud pattern. "
            f"The bank's current authentication methods and transaction monitoring coverage leave "
            f"approximately {assessment.get('gate3_control_gap', {}).get('undetected_percentage', 50):.0f}% "
            f"of attacks undetected. With a composite risk score of {score:.0f}/100, this signal is classified as {priority}."
        ),
        "customer_impact": (
            f"Estimated {at_risk:,} customers at risk, primarily in the {segment} segment. "
            f"Geographic exposure concentrated in {', '.join(geos[:3])}. "
            f"Customers using SMS OTP authentication are particularly vulnerable to this attack vector."
        ),
        "financial_exposure": sim_text,
        "current_control_gaps": (
            f"Existing TM rules provide partial coverage: "
            f"{assessment.get('gate3_control_gap', {}).get('undetected_percentage', 50):.0f}% of attacks would go undetected. "
            f"The fraud typology {label} exploits authentication methods used by the majority of retail customers. "
            f"No real-time behavioural analytics currently flag this specific attack pattern."
        ),
        "recommended_actions": {
            "immediate": [
                f"Issue advisory push notification to at-risk {segment} customers",
                "Activate enhanced monitoring on new payee transfers",
                "Alert fraud operations team for manual review queue",
            ],
            "short_term": [
                f"Submit {typology} TM detection scenario to analytics team",
                "Increase step-up authentication threshold for high-risk transactions",
                "Update customer-facing fraud guidance on website and app",
                "Brief relationship managers on identification and escalation procedure",
            ],
            "strategic": [
                "Accelerate device binding rollout to reduce SMS OTP dependency",
                "Commission technical assessment of real-time behavioral analytics capability",
                f"Develop full response playbook for {label} incidents",
            ],
        },
        "intervention_rules": rules,
        "simulation_summary": sim_text,
        "evidence_sources": fraud_signal.get("raw_evidence", "")[:200] if fraud_signal.get("raw_evidence") else "Intelligence derived from regulatory advisory and open-source threat data.",
        "confidence_rating": "HIGH" if fraud_signal.get("confidence_score", 0) > 0.7 else "MEDIUM",
        "analyst_notes": (
            "IMPORTANT: This alert is AI-generated using synthetic/mock data for POC purposes only. "
            "It must be reviewed by a qualified fraud risk analyst before operational action is taken. "
            f"Data confidence: {fraud_signal.get('confidence_score', 0.5)*100:.0f}%. "
            "All financial figures are estimates derived from synthetic customer population data. "
            "No real UOB customer data was used in this analysis."
        ),
    }


def _generate_with_gemini(
    fraud_signal: Dict,
    assessment: Dict,
    simulation: Optional[Dict],
    rules: List[Dict],
) -> Optional[Dict]:
    """Generate the alert document via Gemini."""
    typology = fraud_signal.get("fraud_typology", "")
    label = TYPOLOGY_LABELS.get(typology, typology)
    at_risk = assessment.get("gate2_customer_exposure", {}).get("estimated_at_risk_customers", 0)
    score = assessment.get("composite_risk_score", 0.0)
    priority = assessment.get("alert_priority", "HIGH")

    fi_text = "Simulation not available."
    if simulation:
        fi = simulation.get("financial_impact", {})
        fi_text = (
            f"Baseline: {_format_sgd(fi.get('baseline_exposure_sgd', 0))}, "
            f"With controls: {_format_sgd(fi.get('with_current_controls_sgd', 0))}, "
            f"With interventions: {_format_sgd(fi.get('with_proposed_controls_sgd', 0))}, "
            f"P10: {_format_sgd(fi.get('p10_sgd', 0))}, P90: {_format_sgd(fi.get('p90_sgd', 0))}"
        )

    doc_schema = """{
  "executive_summary": "3-4 sentences: threat, affected segment, SGD exposure, single most important action",
  "threat_description": "Full fraud narrative: how attack works step-by-step, global emergence, scale",
  "uob_relevance": "Why this matters to UOB specifically: segments, score, gap analysis",
  "customer_impact": "Who is at risk, how many, why they are vulnerable",
  "financial_exposure": "SGD impact narrative with all figures",
  "current_control_gaps": "What existing TM rules miss and why",
  "recommended_actions": {
    "immediate": ["2-4 actions < 24 hours"],
    "short_term": ["3-5 actions 1-7 days"],
    "strategic": ["2-3 actions 1-4 weeks"]
  },
  "simulation_summary": "Summary of simulation results",
  "evidence_sources": ["list of source descriptions"],
  "confidence_rating": "HIGH | MEDIUM | LOW",
  "analyst_notes": "Auto-generated caveats including mandatory disclaimer"
}"""

    user_prompt = f"""Generate a complete Risk Alert Document for the following fraud intelligence.

FRAUD SIGNAL:
- Typology: {label} ({typology})
- Description: {fraud_signal.get('fraud_description', '')}
- Attack Vector: {fraud_signal.get('attack_vector', '')}
- Geographic Origin: {fraud_signal.get('geographic_origin', [])}
- Severity: {fraud_signal.get('severity_estimate', 'HIGH')}
- Novelty Score: {fraud_signal.get('novelty_score', 0.5)}

RELEVANCE ASSESSMENT:
- Overall Priority: {priority}
- Composite Risk Score: {score:.1f}/100
- Gate 1 (Novelty): {"PASSED" if assessment.get("gate1_novelty",{}).get("passed") else "FAILED"} — {assessment.get("gate1_novelty",{}).get("explanation","")}
- Gate 2 (Exposure): {"PASSED" if assessment.get("gate2_customer_exposure",{}).get("passed") else "FAILED"} — {at_risk:,} customers at risk
- Gate 3 (Control Gap): {"PASSED" if assessment.get("gate3_control_gap",{}).get("passed") else "FAILED"} — {assessment.get("gate3_control_gap",{}).get("undetected_percentage",50):.0f}% undetected

FINANCIAL IMPACT:
{fi_text}

INTERVENTION RULES PROPOSED:
{len(rules)} rules generated covering TM_DETECTION, CUSTOMER_FRICTION, POLICY_CHANGE, ADVISORY.

Write a complete Risk Alert Document. Quantify everything in SGD. Name UOB customer segments specifically.
The analyst_notes MUST include: "This alert is AI-generated. It must be reviewed by a qualified fraud risk analyst before operational action is taken."

Return ONLY valid JSON matching this schema:
{doc_schema}"""

    try:
        result = call_gemini(SYSTEM_PROMPT, user_prompt, expect_json=True)
        if isinstance(result, dict) and "executive_summary" in result:
            result["intervention_rules"] = rules
            return result
    except Exception as e:
        logger.warning("Gemini document generation failed: %s", e)
    return None


def generate_alert_document(
    fraud_signal: Dict,
    assessment: Dict,
    simulation: Optional[Dict] = None,
    use_gemini: bool = True,
) -> Dict:
    """
    Generate a complete RiskAlertDocument. Persists to DB and generates PDF.
    Returns the full alert dict.
    """
    fid = fraud_signal.get("fraud_signal_id", str(uuid.uuid4()))
    typology = fraud_signal.get("fraud_typology", "UNKNOWN")
    priority = assessment.get("alert_priority", "HIGH")

    logger.info("Generating alert document for %s (%s) — priority: %s", fid, typology, priority)

    # Generate intervention rules first
    rules = generate_intervention_rules(fraud_signal, assessment, simulation)

    # Generate document content
    doc_content = None
    if use_gemini:
        doc_content = _generate_with_gemini(fraud_signal, assessment, simulation, rules)

    if not doc_content:
        doc_content = _build_fallback_document(fraud_signal, assessment, simulation, rules, priority)

    # Validate required fields
    if not doc_content.get("executive_summary") or len(doc_content["executive_summary"]) < 50:
        doc_content = _build_fallback_document(fraud_signal, assessment, simulation, rules, priority)

    # Ensure disclaimer in analyst_notes
    disclaimer = "This alert is AI-generated. It must be reviewed by a qualified fraud risk analyst before operational action is taken."
    if disclaimer not in doc_content.get("analyst_notes", ""):
        doc_content["analyst_notes"] = disclaimer + " " + doc_content.get("analyst_notes", "")

    # Build routing
    routing = _build_routing(priority, typology)

    # Build alert object
    alert_id = str(uuid.uuid4())
    sim_id = simulation.get("simulation_id") if simulation else None

    alert = {
        "alert_id": alert_id,
        "fraud_signal_id": fid,
        "assessment_id": assessment.get("assessment_id", ""),
        "simulation_id": sim_id,
        "generated_at": datetime.utcnow().isoformat(),
        "priority": priority,
        "document": doc_content,
        "routing": routing,
        "fraud_typology": typology,
        "composite_score": assessment.get("composite_risk_score", 0.0),
    }

    # Generate PDF
    try:
        pdf_path = generate_pdf(alert, fraud_signal, assessment, simulation)
        alert["pdf_path"] = pdf_path
    except Exception as e:
        logger.warning("PDF generation failed: %s", e)
        alert["pdf_path"] = None

    # Persist to database
    insert_risk_alert(alert)
    logger.info("Alert document generated: %s", alert_id)

    return alert
